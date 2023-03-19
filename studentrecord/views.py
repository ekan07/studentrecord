import os
import re
import csv
from pathlib import Path

from flask.wrappers import Request
from studentrecord import app

# from cs50 import SQL
from datetime import datetime
from flask import Flask, flash, redirect, render_template, request, session, Response, url_for, send_from_directory
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
# from studentrecord.helpers import login_required, allowed_image_filesize, allowed_image, reg_pool, email_address_valid, e_message, asign_classcode, school_session
from werkzeug.utils import secure_filename
#####
# from ..models import storage



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
from models.engine.db_storage import mysqlconnect

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

# Create views:


@app.route("/")
# @login_required
def index():
    """ List of class(es) Asign to a teacher """

    try:
        curs, db_connect = mysqlconnect()
        # Executing Query
        curs.execute("SELECT CURDATE();")
        # Above Query Gives Us The Current Date
        # Fetching Data
        m = curs.fetchone()

        # Printing Result Of Above
        print("Today's Date Is ", m[0])
        # Closing Database Connection
        db_connect.close()
        # return("okay")
    except:
        print("Can't connect to database")
        # return 0

# @app.route('/register/', methods=["GET", "POST"])
# def register_page():
    # try:
    #     curs, db_connect = storage()
    #     # Executing Query
    #     curs.execute("SELECT CURDATE();")
    #     # Above Query Gives Us The Current Date
    #     # Fetching Data
    #     m = curs.fetchone()

    #     # Printing Result Of Above
    #     print("Today's Date Is ", m[0])
    #     # Closing Database Connection
    #     db_connect.close()
    #     return("okay")
    # except:
    #     print("Can't connect to database")
    #     return 0




# register_page()
