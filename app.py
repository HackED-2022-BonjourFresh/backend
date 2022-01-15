from functools import wraps
from sqlite3 import IntegrityError
from flask import Flask, make_response, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, exists

from helpers import get_req_arg, login_required

db_name = "test.db"

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_name
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config.from_mapping(
    SECRET_KEY="dev"
)

db = SQLAlchemy(app)

class User(db.Model):
    username = db.Column(db.String(80), primary_key=True)

class Recipe(db.Model):
    name = db.Column(db.String(50), primary_key=True)
    users_recipe = db.Column(db.String(80))

class Ingredient(db.Model):
    name = db.Column(db.String(50), primary_key = True)
    recipe_name = db.Column(db.String(50))

class RecipeIngredient(db.Model):
    recipe_name = db.Column(db.String(50), primary_key=True)
    ingredient_name = db.Column(db.String(50), primary_key=True)
    quantity = db.Column(db.Integer)

db.create_all()

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
        user = User.query.get(username)
        if not user:
            resp = make_response("Error: User not signed up", 400)
            return resp
        session["username"] = username
        resp = make_response(f"{username} is logged in", 200)
        return resp

@app.route("/register_recipe", methods=["POST"])
# @login_required
def register_recipe():
    json = request.get_json()

    username = json["username"]
    recipe_name = json["recipe_name"]
    ingredients = json["ingredients"]

    q = db.session.query(Recipe).filter(Recipe.name == recipe_name and Recipe.users_recipe == username)
    if db.session.query(q.exists()).scalar():
        return "Recipe {} already exists for user {}!".format(recipe_name, username)

    for ingred in ingredients:
        db.session.add(RecipeIngredient(recipe_name=recipe_name, ingredient_name=ingred["name"], quantity=ingred["quantity"]))

    db.session.commit()

    return "OK"

    # query = select(RecipeIngredient).where(RecipeIngredient.recipe_name == recipe_name)
    # ingreds = db.session.execute(query)


    # for ingred in ingredients:
    #     print(ingred)

    # db.sesson.add()

@app.route("/register_recipe_for_user", methods=["GET", "POST"])
def recipes():
    pass

@app.route("/logout")
@login_required
def logout():
    username = session["username"]
    session.clear()
    return make_response(f"{username} is logged out", 200)
