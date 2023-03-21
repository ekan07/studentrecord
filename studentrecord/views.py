import os
import re
import csv
from pathlib import Path

from flask.wrappers import Request
from studentrecord import app

from datetime import datetime
from flask import Flask, flash, redirect, render_template, request, session, Response, url_for, send_from_directory
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from studentrecord.helpers import login_required, allowed_image_filesize, allowed_image, reg_pool, email_address_valid, e_message, asign_classcode, school_session
from werkzeug.utils import secure_filename
#####
# from models.engine.db_storage import mysqlconnect
from models import storage
# used to protect against SQL injection attempts
# from MySQLdb import escape_string as thwart



@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
# db = SQL("sqlite:///studentreg.db")
# from models.engine.db_storage import mysqlconnect

# Generate a secret random key for the session
app.secret_key = os.urandom(24)

CLASSNAMES = [
    "Basic 1",
    "Basic 2",
    "Basic 3",
    "Basic 4",
    "Basic 5"
]

SUBJECTS = {
    "AGRS": "Agricultural Science",
    "ENGL": "English Language",
    "BAST": "Basic Science and Technology",
    "CIVIC": "Civic Education",
    "COMS": "Computer Science",
    "CCA": "Cultural and Creative Art",
    "HEC": "Home Economics",
    "MATH": "Mathematics",
    "PHE": "P.H.E.",
    "SEC": "Security Education",
    "SOS": "Social Studies",
}


@app.route("/")
@login_required
def index():
    """ List of class(es) Asign to a teacher """
    db_connect= storage()
    db_curs = db_connect.cursor()

    userid = session["user_id"]
    print(userid)
    # Query class(es) asigned to teacher
    db_curs.execute("SELECT * FROM classes WHERE id IN (SELECT class_id FROM students WHERE class_id IN (SELECT class_id FROM teachers WHERE userid = %s)) AND id IN (SELECT currentclass_id FROM class_details) ORDER BY class_name",
                         (userid,))
    classes = db_curs.fetchall()
    db_connect.close()
    db_curs.close()
    # db.close()
    return render_template("/index.html", classes=classes)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        missing = list()
        # Ensure username and password are filled in
        for k, v in request.form.items():
            if not v:
                missing.append(k)
        if missing:
            feedback = f"Missing fields for {', '.join(missing)}"
            flash(feedback, "danger")
            return render_template("login.html")
        
        # Query database for username
        db_connect= storage()
        db_curs = db_connect.cursor()
        db_curs.execute("SELECT * FROM users WHERE username = %s",
                          (request.form.get("username"),))
        row = db_curs.fetchone()
        db_curs.close()
        db_connect.close()
        # Ensure username exists:
        if row == None:
            # missing.append("username and/or password not correct")
            feedback = f"username and/or password not correct"
            flash(feedback, "danger")
            return render_template("login.html")
        # Ensure username exists and password is correct
        if row[1] and not check_password_hash(row[2], request.form.get("password")):
            # missing.append("username and/or password not correct")
            feedback = f"username and/or password not correct"
            flash(feedback, "danger")
            return render_template("login.html")
        # Remember which user has logged in
        session["user_id"] = row[0]

        print("\nRedirect to home page\n")

        # Redirect user to home page
        return redirect("/")
    else:

        print("\nRedirect to login\n")

        return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    """sign up User"""

    if request.method == "GET":
        return render_template("/signup.html")
    else:
        username = request.form.get("username").strip()
        password = request.form.get("password").strip()
        # Ensure username and password was submitted (key : value):
        missing = list()
        for k, v in request.form.items():
            if not v:
                missing.append(k)
        if missing:
            feedback = f"Missing fields for {', '.join(missing)}"
            flash(feedback, "danger")
            return render_template("signup.html")
        # Ensure no space in field(s) was submitted:
        for k, v in request.form.items():
            count = 0
            for i in v:
                if i.isspace():
                    count += 1
            if count > 0:
                missing.append(k)
        if missing:
            feedback = f"field(s) can't have space: {', '.join(missing)}"
            flash(feedback, "danger")
            return render_template("signup.html")

        # Query database for username
        db_connect = storage()
        with db_connect.cursor() as db_curs:
            # db_curs = db_connect.cursor()
            db_curs.execute("SELECT * FROM users WHERE username = %s", (username,))
            row = db_curs.fetchone()
            if row == None:
                # Check if passwords matches
                if password != request.form.get("confirmation"):
                    # missing.append("passwords didn't matched")
                    feedback = f"passwords didn't matched"
                    flash(feedback, "danger")

                    print('\nNo match\n')

                    return render_template("signup.html")
                # Hash the password and insert the new user into users database table
                hash = generate_password_hash(password)
                db_curs.execute(
                    "INSERT INTO users (username, password_hash) VALUES(%s, %s)", (username, hash))
                db_connect.commit()
                db_curs.execute("SELECT LAST_INSERT_ID()")
                primary_key = db_curs.fetchone()[0]
                # Login the newly registered user and remember which user has logged in
                session["user_id"] = primary_key
                flash("signed up!", "success")

                print("\nsigned up successfully\n")

                return redirect("/")
            # Check if username not equal to None then username exists
            else:
                if row[1] == username:
                    missing.append(row[1])
                    feedback = f"username {''.join(missing)} used already!"
                    flash(feedback, "danger")

                    print("\nusername exist\n")

                    return render_template("signup.html")
            
        
