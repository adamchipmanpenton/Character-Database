from flask import Flask, render_template, redirect, request, abort, flash, Blueprint, session, url_for, g
from werkzeug.security import check_password_hash, generate_password_hash
from flask_bootstrap import Bootstrap
import sqlite3
import os
from contextlib import closing

application = Flask(__name__)
application.secret_key = 'not a very good key'
application.config["UPLOAD_PATH"] = "static/characters"
application.config['MAX_CONTENT_LENGTH'] = 1024 * 1024
conn = sqlite3.connect("characters.db", check_same_thread=False)
users = sqlite3.connect("users.db", check_same_thread=False)
actUser = []

@application.route("/")
def index():
    return render_template("index.html")

@application.route("/register")
def register():
    return render_template("register.html")

@application.route('/register', methods=["POST"])
def signup():
    firstname = request.values["firstname"]
    lastname = request.values["lastname"]
    email = request.values["email"]
    username = request.values["username"]
    password = request.values["password1"]
    password2 = request.values["password2"]
    if password == password2:
        with closing(users.cursor()) as c:
            query = """SELECT username FROM users"""
            c.execute(query)
            results = c.fetchall()
            listUserNames = []
            for result in results:
                listUserNames.append(result[0])
        for name in listUserNames:
            if name == username:
                flash("Username " + str(username) + " already exists. Try again.")
                return redirect("register")
        with closing(users.cursor()) as c:
            query = """INSERT INTO users (firstname, lastname, email, username, password) VALUES (?, ?, ?, ?, ?)"""
            c.execute(query, (firstname, lastname, email, username, generate_password_hash(password)))
            users.commit()
        return redirect("addCharacter")
    flash("Passwords do not match.")
    return render_template("register.html")

@application.route("/login")
def login():
    if "username" in session:
        flash("Already logged in. Logout first")
    return render_template("login.html")

@application.route("/login", methods=['GET', 'POST'])
def userLogin():
    if request.method == 'POST':
        username = request.values["username"]
        password = request.values["password"]
        with closing(users.cursor()) as c:
            query = """SELECT password FROM users WHERE username = ?"""
            c.execute(query, (username,))
            p = c.fetchone()
            if p != None:
                userPassword = p[0]
                if check_password_hash(userPassword, password):
                    session['username'] = username
                    actUser.append(username)
                    return redirect("addCharacter")
                else:
                    flash("Invalid username or password")
                    return redirect("login")
            else:
                flash("Invalid username or password")
                return redirect("login")

@application.route("/logout")
def logout():
    session.clear()
    actUser.clear()
    return render_template("logout.html")

@application.route("/logout")
def userLogout():
    session.clear()
    return render_template("index.html")

@application.route("/showCharacters")
def showCharacters():
    if "username" in session:
        userName = actUser[0]
        with closing(conn.cursor()) as c:
            query = """SELECT * From characters WHERE username = ?"""
            c.execute(query, (userName,))
            results = c.fetchall()
            images = []
            for result in results:
                images.append((result[0], result[1], result[2], result[3], result[4]))
        return render_template("showCharacters.html", images=images)
    return redirect("login")

@application.route("/showCharacters", methods = ['POST'])
def deleteCharacter():
    characterName = request.values["characterName"]
    query = """SELECT filename FROM characters WHERE charactername = ?"""
    with closing(conn.cursor()) as c:
        c.execute(query, (characterName,))
        file = c.fetchone()
        picture = "static/characters/" + str(file[0]).strip()
    os.remove(picture)
    query = """DELETE FROM characters WHERE charactername = ?"""
    with closing(conn.cursor()) as c:
        c.execute(query, (characterName,))
        conn.commit()
    return redirect("showCharacters")

@application.route("/addCharacter")
def addCharacter():
    if "username" in session:
        return render_template("addCharacter.html")
    return redirect("login")

@application.route("/addCharacter", methods = ['POST'])
def getFormData():
    username = actUser[0]
    uploaded_file = request.files["file"]
    characterName = request.values["characterName"]
    race = request.values["race"]
    characterClass = request.values["class"]
    character_description = request.values["character_description"]
    uploaded_file.save(os.path.join(application.config["UPLOAD_PATH"], uploaded_file.filename))
    with closing(conn.cursor()) as c:
        query = """INSERT INTO characters (filename, charactername, race, class, character_description, username)VALUES (?, ?, ?, ?, ?, ?)"""
        c.execute(query, (uploaded_file.filename, characterName, race, characterClass, character_description, username))
        conn.commit()
    return redirect("showCharacters")