import os
from flask import Flask, render_template, request, redirect, session, url_for
import mysql.connector
import re

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}


def get_db():
    return mysql.connector.connect(**DB_CONFIG)


@app.route("/")
@app.route("/login", methods=["GET", "POST"])
def login():
    msg = ""
    if (
        request.method == "POST"
        and "username" in request.form
        and "password" in request.form
    ):
        username = request.form["username"]
        password = request.form["password"]
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM accounts WHERE username = %s AND password = %s",
            (username, password),
        )
        account = cursor.fetchone()
        cursor.close()
        conn.close()
        if account:
            session["loggedin"] = True
            session["id"] = account["id"]
            session["username"] = account["username"]
            return render_template("index.html", msg="Successful login.")
        else:
            msg = "Incorrect username/password combination."
    return render_template("login.html", msg=msg)


@app.route("/logout")
def logout():
    session.pop("loggedin", None)
    session.pop("id", None)
    session.pop("username", None)
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    msg = ""
    if (
        request.method == "POST"
        and "username" in request.form
        and "password" in request.form
        and "email" in request.form
    ):
        username = request.form["username"]
        password = request.form["password"]
        email = request.form["email"]
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        # checks username
        cursor.execute(
            "SELECT * FROM accounts WHERE username = %s",
            (username,),
        )
        account = cursor.fetchone()

        # checks if there's an acct already for that email
        cursor.execute(
            "SELECT * FROM accounts WHERE email = %s",
            (email,),
        )
        existing_acct = cursor.fetchone()

        if existing_acct:
            msg = "There is already an account associated with that email."
        else:
            if account:
                msg = "That username is not available."
            elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                msg = "Invalid email address."
            elif not re.match(r"[A-Za-z0-9]+", username):
                msg = "Username must contain only letters and numbers."
            elif not username or not password or not email:
                msg = "User must complete all fields to register."
            else:
                cursor.execute(
                    "INSERT INTO accounts VALUES (NULL, %s, %s, %s)",
                    (username, password, email),
                )
                conn.commit()
                cursor.close()
                conn.close()
                msg = "You have successfully registered!"
    return render_template("register.html", msg=msg)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
