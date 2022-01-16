from sqlite3 import IntegrityError

from flask import Flask, jsonify, make_response, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError

from helpers import (login_required, 
                     merge_ingreds, 
                     ingred_unit_is_known, 
                     attempt_to_conv_type_to_known_type, 
                     get_amount)

DB_NAME = "test.db"

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + DB_NAME
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config.from_mapping(
    SECRET_KEY="dev"
)

db = SQLAlchemy(app)


# ------------- DB Definitions -----------------------

class User(db.Model):
    username = db.Column(db.String(80), primary_key=True)

class UsersRecipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Integer, db.ForeignKey("user.username"))
    recipe_name = db.Column(db.String(100), db.ForeignKey("recipe.name"))
    date = db.Column(db.String(100))

class Recipe(db.Model):
    name = db.Column(db.String(100), primary_key=True)
    instructions = db.Column(db.Text)
    url_image = db.Column(db.Text)

class RecipeIngredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recipe_name = db.Column(db.String(100), db.ForeignKey("recipe.name"))
    ingredient_name = db.Column(db.String(100))
    amount = db.Column(db.Float)
    unit = db.Column(db.String(50))

db.create_all()


# ------------- Endpoints --------------------

@app.route("/")
def hello():
    return "hello world"

@app.route("/sign_up", methods=["POST"])
def sign_up():
    if request.method == "POST":
        try:
            username = request.get_json(force=True)["username"]
            user = User(username=username)
            session["username"] = username
            db.session.add(user)
            db.session.commit()
            return make_response(f"{username} is registered and logged in", 200)
        except IntegrityError:
            resp = make_response("Error: User already in database", 400)
            return resp

@app.route("/login", methods=["POST"])
def login():
    if request.method == "POST":
        username = request.get_json(force=True)["username"]
        user = User.query.filter_by(username=username).first()
        if not user:
            resp = make_response("Error: User not signed up", 400)
            return resp
        session["username"] = username
        resp = make_response(f"{username} is logged in", 200)
        return resp

@app.route("/register_recipe", methods=["POST"])
def register_recipe():
    if request.method == "POST":
        json = request.get_json(force=True)

        recipe_name = json["title"]
        ingredients = json["extendedIngredients"]
        instructions = get_instructions(json)
        url_image = json["image"]

        q = db.session.query(Recipe).filter(Recipe.name == recipe_name)
        if db.session.query(q.exists()).scalar():
            return "Recipe {} already exists!".format(recipe_name)

        db.session.add(Recipe(name=recipe_name, instructions=instructions, url_image=url_image))

        for ingred in ingredients:            
            name = ingred["name"]
            amount = ingred["amount"]
            unit = attempt_to_conv_type_to_known_type(ingred["unit"].lower())
            db.session.add(RecipeIngredient(recipe_name=recipe_name, ingredient_name=name, amount=amount, unit=unit))

        db.session.commit()

        return make_response("Entered recipe", 200)

@app.route("/recipes_for_user", methods=["GET", "POST"])
@login_required
def recipe_for_user():
    if request.method == "POST":
        json = request.get_json(force=True)
        username = session["username"]
        recipe_name = json["recipe_name"]
        date = json["date"]
        q = UsersRecipe.query.filter_by(username=username, recipe_name=recipe_name).first()
        if q is not None:
            return make_response("Recipe already registered for user", 400)
        else:
            db.session.add(UsersRecipe(username=username, recipe_name=recipe_name, date=date))
            db.session.commit()
            return make_response("Entered recipe for user", 200)
    
    if request.method == "GET":
        username = session["username"]
        query = UsersRecipe.query.filter_by(username=username).all()
        user_recipes=[]
        for q in query:
            if Recipe.query.filter_by(name=q.recipe_name).first() is None:
                continue
            recipe = {"recipe_name": q.recipe_name,
                     "date": q.date, 
                     "instruction": Recipe.query.filter_by(name=q.recipe_name).first().instructions,
                     "image": Recipe.query.filter_by(name=q.recipe_name).first().url_image
            }
            ingredients = RecipeIngredient.query.filter_by(recipe_name=q.recipe_name).all()
            ingredients_list = []
            for i in ingredients:
                ingredients_list.append({"name":i.ingredient_name, "amount": "{:2}".format(i.amount), "unit": i.unit})
            recipe["ingredients"] = ingredients_list

            user_recipes.append(recipe)

        return jsonify(user_recipes)

@app.route("/grocery_list_for_user", methods=["GET"])
@login_required
def gen_grocery_list():
    recipes = recipe_for_user().get_json(force=True)

    agg_ingreds = {}
    for ingred_list in map(lambda r: r["ingredients"], recipes):
        for ingred in ingred_list:
            ingred_name = ingred["name"]

            if ingred_name not in agg_ingreds:
                agg_ingreds[ingred_name] = {}
                agg_ingreds[ingred_name]["known"] = None
                agg_ingreds[ingred_name]["unknown"] = []
                add_agg_ingred_to_dict(agg_ingreds, ingred)
            elif agg_ingreds[ingred_name]["known"] is not None and ingred_unit_is_known(ingred):
                try:
                    existing_ingred_quantity = agg_ingreds[ingred_name]["known"]
                    amt, units = merge_ingreds(ingred, existing_ingred_quantity)
                    agg_ingreds[ingred_name]["known"]["amount"] = amt
                    agg_ingreds[ingred_name]["known"]["unit"] = units
                except:
                    add_ingred_to_unknown(agg_ingreds, ingred)
            else:
                add_ingred_to_unknown(agg_ingreds, ingred) 


    return jsonify(compact_grocery_list(agg_ingreds))


@app.route("/grocery_list_for_user/random", methods=["GET"])
@login_required
def get_grocery_list():
    recipes = recipe_for_user().get_json(force=True)
    grocery_list = []
    ingredients = []
    for i in recipes:
        for j in i["ingredients"]:
            if j["name"] not in ingredients:
                ingredients.append(j["name"])
                amount, unit = get_amount()
                grocery_list.append({"name": j["name"],
                                     "amount": amount,
                                     "unit": unit})

    return jsonify(grocery_list)

@app.route("/logout")
@login_required
def logout():
    username = session["username"]
    session.clear()
    return make_response(f"{username} is logged out", 200)


def get_instructions(json):
    instructions = []
    for inst in json["analyzedInstructions"][0]["steps"]:
        line = f'{inst["number"]}. {inst["step"]}'
        instructions.append(line)
    return "\n".join(instructions)


def compact_grocery_list(agg_ingredients):
    grocery_list = []
    for name in agg_ingredients:
        if agg_ingredients[name]["known"] is not None and not agg_ingredients[name]["unknown"]:
            grocery_list.append({
                "name": name,
                "amount": agg_ingredients[name]["known"]["amount"],
                "unit": agg_ingredients[name]["known"]["unit"]
            })
        elif agg_ingredients[name]["known"] is None and agg_ingredients[name]["unknown"]:
            unknown = agg_ingredients[name]["unknown"]
            amount, unit = list(unknown[0].split(" ")) if len(unknown) == 1 else (unknown, "")
            grocery_list.append({
                "name": name,
                "amount": amount,
                "unit": unit
            })
        else:
           grocery_list.append({
                "name": name,
                "amount": agg_ingredients[name]["known"]["amount"],
                "unit": agg_ingredients[name]["known"]["unit"],
                "extra": agg_ingredients[name]["unknown"]
            }) 

    return grocery_list
    
def remove_name(ingredient):
    new_ingredient = {}
    for i in ingredient:
        if i != "name":
            new_ingredient[i] = ingredient[i]
    return new_ingredient

def add_agg_ingred_to_dict(agg_ingreds, ingred):
    if ingred_unit_is_known(ingred):
        agg_ingreds[ingred["name"]]["known"] = remove_name(ingred)
    else:
        add_ingred_to_unknown(agg_ingreds, ingred)

def add_ingred_to_unknown(agg_ingreds, ingred):
    agg_ingreds[ingred["name"]]["unknown"].append(str(ingred["amount"]) +" "+ str(ingred["unit"]))
