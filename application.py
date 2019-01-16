import os
import requests


from flask import Flask, session, render_template, request, session, Markup
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_sqlalchemy import SQLAlchemy

from classes import User

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/", methods=["GET", "POST"])
def index():
    if session.get("user") is None:
        login_message=('')
        if request.method=="POST":
            login_message=('Please login to search for a book')
        return render_template("nouser.html", login_message=login_message)
    else:
        session["books"]=[]   
        if request.method=="POST":
            message=('')
            text=request.form.get('text') 
            data=db.execute("SELECT * FROM books WHERE author iLIKE '%"+text+"%' OR title iLIKE '%"+text+"%' OR isbn iLIKE '%"+text+"%'").fetchall()
            for x in data:
                session['books'].append(x)
            if len(session["books"])==0:
                message=('Nothing found. Try again.')
        return render_template("index.html", data=session['books'])

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        message=('')
        username = request.form.get("username")
        password = request.form.get("password")
        result = db.execute("SELECT id, name, email, username, password FROM users WHERE username=:username AND password=:password", {"username": username, "password": password}).fetchone()
        if result is None:
        	return render_template("login.html", message="Username or password incorrect")
        else:
            user = User(result.id, result.name, result.email, result.username, result.password)

        if user:
            session["user"] = user
            return render_template("index.html")

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == 'GET':
        return render_template("register.html")
    else:
        name = request.form.get("name")
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        db.execute("INSERT INTO users(name, email, username, password) VALUES (:name, :email, :username, :password)", {"name": name, "email": email, "username": username, "password": password})
        db.commit()
        return render_template("login.html")

@app.route("/logout")
def logout():
    session["user"] = None
    return index()

@app.route("/<string:title>/<string:isbn>", methods=["GET", "POST"])
def books(title, isbn):
    KEY = "pzHcos7jNpeLoSZ6y8NhA"
    message = ""
    username = session["user"].username
    session['reviews']=[]
    existing_review = db.execute("Select * From reviews WHERE isbn = :isbn AND username = :username", {"isbn": isbn, "username": username}).fetchone()
    if request.method=="POST":
        if existing_review:
            message = "You may only submit one review per book."
        else:
            review=request.form.get('textarea')
            rating=request.form.get('stars') 
            db.execute("INSERT INTO reviews (isbn, review, rating, username) VALUES (:a,:b,:c,:d)",{"a":isbn,"b":review,"c":rating,"d":username})
            db.commit()

    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": KEY, "isbns": isbn}) 
    avg_rating = res.json()['books'][0]['average_rating']
    rtngs_count = res.json()['books'][0]['ratings_count']
    reviews=db.execute("SELECT * FROM reviews WHERE isbn = :isbn",{"isbn":isbn}).fetchall() 
    for y in reviews:
        session['reviews'].append(y)
    data=db.execute("SELECT * FROM books WHERE isbn = :isbn",{"isbn":isbn}).fetchone()
    return render_template("book.html", data=data, reviews=session['reviews'], username=username, message=message, avg_rating=avg_rating, rtngs_count=rtngs_count)


@app.route("/api/<string:isbn>")
def api(isbn):
    KEY = "pzHcos7jNpeLoSZ6y8NhA"


