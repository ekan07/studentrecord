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
    db_curs.close()
    db_connect.close()
    # db.close()
    return render_template("/index.html", classes=classes)


@app.route("/download_csv/<int:class_id>", methods=["GET", "POST"])
@login_required
def download_csv(class_id):
    """ download csv files of list of students in a specified class """
    db_connect= storage()
    db_curs = db_connect.cursor()

    # Query students in a specified class
    user_id = session['user_id']
    id = class_id
    db_curs.execute("SELECT reg_num as admission_number, surname, othername, gender FROM people JOIN students ON people.id = students.person_id JOIN classes ON students.class_id = classes.id JOIN teachers ON classes.id = teachers.class_id WHERE teachers.userid = %s AND classes.id = %s",
                          (user_id, id))
    students = db_curs.fetchall()
    if len(students) == None:
        return e_message("Not authorized", 404)
    db_curs.execute("SELECT class_name FROM classes WHERE id = :id", (id,))
    classRow = db_curs.fetchone()
    db_curs.close()
    db_connect.close()
    # field names
    fields = ['admission_number', 'surname', 'othername', 'gender']
    # name for csv file to be created
    filename = classRow[1] + ".csv"
    # writing to csv file
    csv_path = Path("studentrecord", "static", "client", "csv")
    with open(Path(csv_path, filename), 'w', encoding="utf-8") as csvfile:
        # creating a csv dict writer object
        writer = csv.DictWriter(csvfile, fieldnames=fields)
        # writing headers (field names)
        writer.writeheader()
        # writing data rows
        writer.writerows(students)
    # Download the csv file
    return send_from_directory(app.config["CLIENT_CSV"], Path(csv_path, filename), as_attachment=True)


@app.route("/<int:class_id>", methods=["GET", "POST"])
@login_required
def classStudents(class_id):
    """ List of students in a class """
    db_connect= storage()
    db_curs = db_connect.cursor()

    # Query students in a specified class
    userid = session['user_id']
    id = class_id
    db_curs.execute("SELECT reg_num, surname, othername, gender FROM people JOIN students ON people.id = students.person_id JOIN classes ON students.class_id = classes.id JOIN teachers ON classes.id = teachers.class_id WHERE teachers.userid = %s AND classes.id = %s",
                          (userid, id))
    students = db_curs.fetchall()
    db_curs.close()
    db_connect.close()
    if len(students) == None:
        return e_message("Not authorized", 404)
    return render_template("/classstudents.html", students=students)


@app.route("/studentprofile/<int:student_regnum>")
@login_required
def studentprofile(student_regnum):
    """ Display student details on page """
    db_connect= storage()
    with db_connect.cursor() as db_curs:

        # Query for student's details
        reg_num = student_regnum
        db_curs.execute("SELECT * FROM people JOIN students ON people.id = students.person_id JOIN classes ON students.class_id = classes.id JOIN teachers ON classes.id = teachers.class_id JOIN class_details ON class_details.currentclass_id = classes.id GROUP BY students.reg_num, class_details.currentclass_id HAVING students.reg_num = %s",
                                    (reg_num,))
        studentDocument = db_curs.fetchone()
        if len(studentDocument) == None:
            return e_message("Invalid url link", 404)
        db_curs.execute("SELECT * FROM images WHERE regnum_id = %s", (reg_num,))
        image = db_curs.fetchone()
        # Use default image if no uploaded picture
        if len(image) == None:
            # gender [3]
            if studentDocument[3].lower() == 'female':
                # Image storage path
                imgFilePath = "img/default/female.png"
            elif studentDocument[3].lower() == 'male':
                # Image storage path
                imgFilePath = "img/default/male.jpg"
        else:
            # Split the extension from the filename (mimetype [3])
            img_exsn = image[3]["mimetype"].rsplit("/", 1)[1]
            # Image storage path (regnum_id [1])
            imgFilePath = "img/uploads/basic/" + \
                str(image[1]) + "." + img_exsn
            # Write image to storage path (image [2])
            with open("studentrecord/static/" + imgFilePath, "wb") as file:
                file.write(image[2])
        
        entryclass_id = studentDocument[20]["entryclass_id"],
        db_curs.execute("SELECT class_name FROM classes WHERE id = %s",
                                (entryclass_id,))
        entryClass = db_curs.fetchone()

        currentclass_id = studentDocument[21]
        db_curs.execute("SELECT class_name FROM classes WHERE id = %s",
                                (currentclass_id,))
        currentClass = db_curs.fetchone()

        regnum_id=student_regnum
        db_curs.execute("SELECT * FROM guardians WHERE regnum_id = :regnum_id", (regnum_id,))
        guardian = db_curs.fetchone()

    db_connect.close()
    return render_template("/studentprofile.html", imgfile=imgFilePath, studentdocument=studentDocument[0], entryclass=entryClass,
                           currentclass=currentClass, guardian=guardian)


@app.route("/asign_classteacher", methods=["GET", "POST"])
@login_required
def asign_classteacher():
    """ Asign class to teacher """

    if request.method == "POST":
        className = request.form.get("classname")
        missing = list()
        # Ensure field(s) was submitted (key : value):
        # -------------------------------------------
        for k, v in request.form.items():
            if not v:
                missing.append(k)
        if missing:
            flash(f"Missing fields for {', '.join(missing)}", "danger")
            return redirect("/asign_classteacher")

        if className == None:
            flash("Please select class name", "danger")
            return redirect("/asign_classteacher")
        # Ensure that class name exist
        if className not in CLASSNAMES:
            return e_message("Invalid Class Name", 404)
        
        # ALX: change this classID to classcode
        classID = int(asign_classcode(className))

        db_connect= storage()
        with db_connect.cursor() as db_curs:
            # db_curs = db_connect.cursor()
            # Ensure class exist and teacher is not asign to a particular class more than once:
            db_curs.execute(
                "SELECT * FROM classes WHERE class_name = %s", (className,))
            classRow = db_curs.fetchone()
            userid = session['user_id']
            if len(classRow) != None:
                class_id = classRow[0]
                db_curs.execute("SELECT * FROM teachers WHERE class_id = %s AND userid = %s",
                                        (class_id, userid))
                teacherRows = db_curs.fetchone()
                if len(teacherRows) != None:
                    # 'class_name' [1]
                    flash(f"{classRow[1]} already asigned", "danger")
                    return redirect("/asign_classteacher")
                else:
                    # Asign class to teacher
                    db_curs.execute("INSERT INTO teachers (class_id, userid) VALUES(%s, %s)",
                            (class_id, userid))
                    db_curs.commit()
                    flash(f"{classRow[1]} asigned", "success")
                    return redirect("/")
            else:
                # Asign class
                id = classID
                class_name = className
                db_curs.execute("INSERT INTO classes (id, class_name) VALUES(%s, %s)",
                        (id, class_name))
                # Asign class to teacher
                db_curs.execute("INSERT INTO teachers (class_id, userid) VALUES(%s, %s)",
                        (id, userid))
                db_curs.commit()
                flash(f"{className} asigned", "success")
                return redirect("/")

    classnames = CLASSNAMES
    # asign_classcode(classname)
    return render_template("/classteacher.html", classnames=classnames)


@app.route("/bsubjects")
@login_required
def bsubjects():
    """ Get class(es) asigned to teacher """
    
    db_connect= storage()
    with db_connect.cursor() as db_curs:
        userid=session["user_id"]
        # Get class(es) asigned to teacher
        db_curs.execute("SELECT class_name FROM classes JOIN teachers ON classes.id = teachers.class_id JOIN class_details ON class_details.currentclass_id = classes.id WHERE teachers.userid = %s GROUP BY class_details.currentclass_id",
                            (userid,))
        classRows = db_curs.fetchone()
        ASIGNEDCLASSES = []
        for classRow in classRows:
            for classname in CLASSNAMES:
                # "class_name"
                if classRow[0] == classname:
                    ASIGNEDCLASSES.append(classname)
    return render_template("/bsubjects.html", asignedclasses=ASIGNEDCLASSES, subjects=SUBJECTS)


@app.route("/bsubject", methods=["GET", "POST"])
@login_required
def bsubject():
    """ Asign subject to a class """
    db_connect= storage()
    db_curs = db_connect.cursor()

    if request.method == "POST":
        # Get class(es) asigned to teacher
        userid = session["user_id"]
        db_curs.execute("SELECT classes.id, class_name FROM classes JOIN teachers ON classes.id = teachers.class_id JOIN class_details ON class_details.currentclass_id = classes.id WHERE teachers.userid = :userid GROUP BY class_details.currentclass_id",
                               (userid,))
        classRows = db_curs.fetchall()
        ASIGNEDCLASSES = []
        for classRow in classRows:
            # "class_name"
            if classRow[1] in CLASSNAMES:
                ASIGNEDCLASSES.append(classRow[1])

        subjectCode = request.form.get("subjectcode")
        className = request.form.get("classname")
        # Ensure subject and class name is selected
        if subjectCode == None:
            flash(f"Please select subject", "danger")
            return redirect("/bsubjects")
        if className == None:
            flash(f"Please select class name", "danger")
            return redirect("/bsubjects")
        # Ensure selected subject and class name exist in the server
        if subjectCode not in SUBJECTS:
            return e_message("Invalid Subject", 404)
        if className not in ASIGNEDCLASSES:
            return e_message("Invalid Class Name", 404)

        # Insert data into b_subject table
        for classRow in classRows:
            # "class_name"
            if classRow[1] == className:
                # Check if subject has been asigned to a class
                subject_name = SUBJECTS[subjectCode]
                class_id = classRow[0]
                db_curs.execute("SELECT * FROM b_subjects WHERE subject_name = %s AND class_id = %s LIMIT 1",
                                        (subject_name, class_id))
                subjectRow = db_curs.fetchone
                if len(subjectRow) == 1:
                    flash(
                        f"{SUBJECTS[subjectCode]} subject already asigned to {className}", "danger")
                    return redirect("/bsubjects")
                # Else asign subject to a class
                subject_name = SUBJECTS[subjectCode]
                db_curs.execute("INSERT INTO b_subjects (subject_name, subject_code, teacher_id, class_id) VALUES(%s, %s, %s, %s)",
                           (subject_name, subjectCode, userid, class_id))
                db_curs.commit()
                flash(
                    f"{SUBJECTS[subjectCode]} subject asigned to {className}", "success")
                return redirect("/bsubjects")


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
        with db_connect.cursor() as db_curs:
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
            
        
