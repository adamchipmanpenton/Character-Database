from flask import Flask, render_template, redirect, request, abort, flash, Blueprint, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash


from flask_bootstrap import Bootstrap
import sqlite3
import os
from contextlib import closing

app = Flask(__name__)
app.secret_key = 'super secret key'
app.config["UPLOAD_PATH"] = "static/characters"
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024
conn = sqlite3.connect("characters.db", check_same_thread=False)
users = sqlite3.connect("users.db", check_same_thread=False)


@app.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()


@app.route('/register', methods=["POST"])
def signup():
    username = request.values["username"]
    password = request.values["password"]
    with closing(users.cursor()) as c:
        query = """INSERT INTO users (username, password) VALUES (?, ?)"""
        c.execute(query, (username, generate_password_hash(password)))
        users.commit()
    return redirect("addCharacter")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/login", methods=['GET', 'POST'])
def userLogin():
    if request.method == 'POST':
        username = request.values["username"]
        password = request.values["password"]
        with closing(users.cursor()) as c:
            query = """SELECT password FROM users WHERE username = ?"""
            c.execute(query, (username,))
            p = c.fetchone()
            userPassword = p[0]
        if check_password_hash(userPassword, password):
            session['username'] = username
            return redirect("addCharacter")
        else:
            flash("Invalid username or password")
            return redirect("login")

@app.route("/logout")
def logout():
    return render_template("logout.html")

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/showCharacters")
def showCharacters():
    with closing(conn.cursor()) as c:
        query = """SELECT * From characters"""
        c.execute(query)
        results = c.fetchall()
        images = []
        for result in results:
            images.append((result[0], result[1], result[2], result[3], result[4]))
    return render_template("showCharacters.html", images=images)

@app.route("/showCharacters", methods = ['POST'])
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

@app.route("/addCharacter")
def addCharacter():
    return render_template("addCharacter.html")

@app.route("/addCharacter", methods = ['POST'])
def getFormData():
    uploaded_file = request.files["file"]
    characterName = request.values["characterName"]
    race = request.values["race"]
    characterClass = request.values["class"]
    character_description = request.values["character_description"]
    if uploaded_file.filename != " ":
        #file_ext = os.path.splitext(uploaded_file)[1]
        #if file_ext not in app.config['UPLOAD_EXTENSIONS']:
         #   abort(400)
        uploaded_file.save(os.path.join(app.config["UPLOAD_PATH"], uploaded_file.filename))
        with closing(conn.cursor()) as c:
            query = """INSERT INTO characters (filename, charactername, race, class, character_description)VALUES (?, ?, ?, ?, ?)"""
            c.execute(query, (uploaded_file.filename, characterName, race, characterClass, character_description))
            conn.commit()
    return redirect("showCharacters")