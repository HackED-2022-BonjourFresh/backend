from curses.ascii import US
from dis import Instruction
from enum import unique
from functools import wraps
from sqlite3 import IntegrityError
from flask import Flask, jsonify, make_response, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from markupsafe import re
from sqlalchemy.exc import IntegrityError
from sqlalchemy import ForeignKey, select, exists

from helpers import get_req_arg, login_required, merge_ingreds

db_name = "test.db"

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_name
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
    quantity = db.Column(db.Integer)

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
#@login_required
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

            amount, unit = ingred["amount"], ingred["unit"]
            quantity = f"{amount} {unit}"
            name = ingred["name"]

            db.session.add(RecipeIngredient(recipe_name=recipe_name, ingredient_name=name, quantity=quantity))

        db.session.commit()

        return make_response("Entered recipe", 200)


@app.route("/recipes_for_user", methods=["GET", "POST"])
@login_required
def recipe_for_user():
    if request.method == "POST":
        json = request.get_json(force=True)
        username = session["username"]
        #username = json["username"]
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
        username  = session["username"]
        query = UsersRecipe.query.filter_by(username=username).all()
        user_recipes=[]
        for q in query:
            recipe = {"recipe_name": q.recipe_name,
                     "date": q.date, 
                     "instruction": Recipe.query.filter_by(name=q.recipe_name).first().instructions,
                     "image": Recipe.query.filter_by(name=q.recipe_name).first().url_image
            }
            ingredients = RecipeIngredient.query.filter_by(recipe_name=q.recipe_name).all()
            ingredients_list = []
            for i in ingredients:
                ingredients_list.append({"name":i.ingredient_name, "quantity": i.quantity})
            recipe["ingredients"] = ingredients_list

            user_recipes.append(recipe)

        return jsonify(user_recipes)

@app.route("/grocery_list_for_user", methods=["GET"])
#@login_required
def gen_grocery_list():
    recipes = recipe_for_user()

    agg_ingreds = {}
    for ingred in map(lambda r: r.ingredients, recipes):
        if ingred["name"] not in agg_ingreds:
            agg_ingreds["name"] = ingred["quantity"]
        else:
            existing_ingred_quantity = ingred["name"]
            agg_ingreds["name"] = merge_ingreds(ingred, existing_ingred_quantity)

    return jsonify(agg_ingreds)

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

