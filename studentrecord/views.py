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
from models import storage
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

    userid = session["user_id"]
    db_connect = storage()
    db_curs = db_connect.cursor()
    # Query class(es) asigned to teacher
    db_curs.execute("""
                    SELECT * FROM classes WHERE id
                    IN (SELECT class_id FROM students WHERE class_id
                    IN (SELECT class_id FROM teachers WHERE userid = %s))
                    AND id IN (SELECT currentclass_id FROM class_details)
                    ORDER BY class_name""", (userid,))
    classes = db_curs.fetchall()
    db_curs.close()
    db_connect.close()
    return render_template("/index.html", classes=classes)


@app.route("/download_csv/<int:class_id>", methods=["GET", "POST"])
@login_required
def download_csv(class_id):
    """ download csv files of list of students in a specified class """

    user_id = session['user_id']
    id = class_id
    db_connect = storage()
    db_curs = db_connect.cursor()
    # Query students in a specified class
    db_curs.execute("""
                    SELECT reg_num as admission_number, surname, othername, gender FROM people
                    JOIN students ON people.id = students.person_id
                    JOIN classes ON students.class_id = classes.id
                    JOIN teachers ON classes.id = teachers.class_id WHERE teachers.userid = %s
                    AND classes.id = %s""", (user_id, id))
    students = db_curs.fetchall()
    if len(students) == None:
        return e_message("Not authorized", 404)
    db_curs.execute("SELECT class_name FROM classes WHERE id = %s", (id,))
    classRow = db_curs.fetchone()
    db_curs.close()
    db_connect.close()
    fields = ['admission_number', 'surname', 'othername', 'gender']
    # name for csv file to be created
    filename = classRow[0] + ".csv"
    csv_path = Path("studentrecord", "static", "client", "csv")
    with open(Path(csv_path, filename), 'w', encoding="utf-8") as csvfile:
        # creating a csv writer object
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(fields)
        csvwriter.writerows(students)
    # Download the csv file
    return send_from_directory(app.config["CLIENT_CSV"], Path(csv_path, filename), as_attachment=True)


@app.route("/<int:class_id>", methods=["GET", "POST"])
@login_required
def classStudents(class_id):
    """ List of students in a class """

    userid = session['user_id']
    id = class_id
    db_connect = storage()
    db_curs = db_connect.cursor()
    # Query students in a specified class
    db_curs.execute("""
                    SELECT reg_num, surname, othername, gender FROM people
                    JOIN students ON people.id = students.person_id
                    JOIN classes ON students.class_id = classes.id
                    JOIN teachers ON classes.id = teachers.class_id WHERE teachers.userid = %s
                    AND classes.id = %s""", (userid, id))
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
    db_connect = storage()
    with db_connect.cursor() as db_curs:
        reg_num = student_regnum
        # Query for student's details
        db_curs.execute("""
                        SELECT
                        reg_num, ANY_VALUE(surname), ANY_VALUE(othername), ANY_VALUE(gender), ANY_VALUE(date_of_birth),
                        ANY_VALUE(states), ANY_VALUE(nationality), ANY_VALUE(religion), ANY_VALUE(admsn_date),
                        ANY_VALUE(entryclass_id), currentclass_id, ANY_VALUE(class_status), ANY_VALUE(trans_grad_date)
                        FROM people JOIN students ON people.id = students.person_id
                        JOIN classes ON students.class_id = classes.id
                        JOIN teachers ON classes.id = teachers.class_id
                        JOIN class_details ON class_details.currentclass_id = classes.id
                        GROUP BY students.reg_num, class_details.currentclass_id
                        HAVING students.reg_num = %s""", (reg_num,))
        studentDocument = db_curs.fetchone()
        if studentDocument == None:
            return e_message("Invalid url link", 404)
        db_curs.execute(
            "SELECT * FROM images WHERE regnum_id = %s", (reg_num,))
        image = db_curs.fetchone()
        # Use default image if no uploaded picture
        if image == None:
            if studentDocument[3].lower() == 'female':
                # Image storage path
                imgFilePath = "img/default/female.png"
            elif studentDocument[3].lower() == 'male':
                imgFilePath = "img/default/male.jpg"
        else:
            # Split the extension from the filename (mimetype [3])
            img_exsn = image[3].rsplit("/", 1)[1]
            imgFilePath = "img/uploads/basic/" + \
                str(image[1]) + "." + img_exsn
            # Write image to storage path (image [2])
            with open("studentrecord/static/" + imgFilePath, "wb") as file:
                file.write(image[2])
        entryclass_id = studentDocument[9],
        db_curs.execute("SELECT class_name FROM classes WHERE id = %s",
                        (entryclass_id,))
        entryClass = db_curs.fetchone()
        currentclass_id = studentDocument[10]
        db_curs.execute("SELECT class_name FROM classes WHERE id = %s",
                        (currentclass_id,))
        currentClass = db_curs.fetchone()
        regnum_id = student_regnum
        db_curs.execute(
            "SELECT * FROM guardians WHERE regnum_id = %s", (regnum_id,))
        guardian = db_curs.fetchone()

    db_connect.close()
    return render_template("/studentprofile.html", imgfile=imgFilePath,
                           studentdocument=studentDocument, entryclass=entryClass,
                           currentclass=currentClass, guardian=guardian)


@app.route("/asign_classteacher", methods=["GET", "POST"])
@login_required
def asign_classteacher():
    """ Asign class to teacher """

    if request.method == "POST":
        className = request.form.get("classname")
        missing = list()
        # Ensure field(s) was submitted (key : value):
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

        classID = int(asign_classcode(className))
        userid = session['user_id']
        db_connect = storage()
        with db_connect.cursor() as db_curs:
            db_curs.execute(
                "SELECT * FROM classes WHERE class_name = %s", (className,))
            classRow = db_curs.fetchone()
            # Ensure class exist and teacher is not asign to a particular class more than once:
            if classRow != None:
                class_id = classRow[0]
                db_curs.execute("SELECT * FROM teachers WHERE class_id = %s AND userid = %s",
                                (class_id, userid))
                teacherRows = db_curs.fetchone()
                if len(teacherRows) != None:
                    flash(f"{classRow[1]} already asigned", "danger")
                    return redirect("/asign_classteacher")
                else:
                    # Asign class to teacher
                    db_curs.execute("INSERT INTO teachers (class_id, userid) VALUES(%s, %s)",
                                    (class_id, userid))
                    db_connect.commit()
                    flash(f"{classRow[1]} asigned", "success")
                    return redirect("/")
            else:
                id = classID
                class_name = className
                # Asign class
                db_curs.execute("INSERT INTO classes (id, class_name) VALUES(%s, %s)",
                                (id, class_name))
                # Asign class to teacher
                db_curs.execute("INSERT INTO teachers (class_id, userid) VALUES(%s, %s)",
                                (id, userid))
                db_connect.commit()
                flash(f"{className} asigned", "success")
                return redirect("/")

    classnames = CLASSNAMES
    # asign_classcode(classname)
    return render_template("/classteacher.html", classnames=classnames)


@app.route("/bsubjects")
@login_required
def bsubjects():
    """ Get class(es) asigned to teacher """

    db_connect = storage()
    with db_connect.cursor() as db_curs:
        userid = session["user_id"]
        # Get class(es) asigned to teacher
        db_curs.execute("""
                        SELECT class_name FROM classes JOIN teachers ON classes.id = teachers.class_id
                        JOIN class_details ON class_details.currentclass_id = classes.id
                        WHERE teachers.userid = %s
                        GROUP BY class_details.currentclass_id""", (userid,))
        classRows = db_curs.fetchall()

        print(f'\nclassRows: {classRows}\n')

        ASIGNEDCLASSES = []
        for classRow in classRows:
            for classname in CLASSNAMES:
                if classRow[0] == classname:
                    ASIGNEDCLASSES.append(classname)
    return render_template("/bsubjects.html", asignedclasses=ASIGNEDCLASSES, subjects=SUBJECTS)


@app.route("/bsubject", methods=["GET", "POST"])
@login_required
def bsubject():
    """ Asign subject to a class """

    if request.method == "POST":
        userid = session["user_id"]
        db_connect = storage()
        db_curs = db_connect.cursor()
        # Get class(es) asigned to teacher
        db_curs.execute("""
                        SELECT classes.id, class_name FROM classes
                        JOIN teachers ON classes.id = teachers.class_id
                        JOIN class_details ON class_details.currentclass_id = classes.id
                        WHERE teachers.userid = %s GROUP BY class_details.currentclass_id
                        """, (userid,))
        classRows = db_curs.fetchall()
        ASIGNEDCLASSES = []
        for classRow in classRows:
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
            if classRow[1] == className:
                subject_name = SUBJECTS[subjectCode]
                class_id = classRow[0]
                db_curs.execute("SELECT * FROM b_subjects WHERE subject_name = %s AND class_id = %s LIMIT 1",
                                (subject_name, class_id))
                subjectRow = db_curs.fetchone()
                # Check if subject has been asigned to a class
                if subjectRow != None:
                    flash(
                        f"{SUBJECTS[subjectCode]} subject already asigned to {className}", "danger")
                    return redirect("/bsubjects")
                # Else asign subject to a class
                subject_name = SUBJECTS[subjectCode]
                db_curs.execute("""
                                INSERT INTO b_subjects (subject_name, subject_code, teacher_id, class_id)
                                VALUES(%s, %s, %s, %s)""", (subject_name, subjectCode, userid, class_id))
                db_connect.commit()
                db_curs.close()
                db_connect.close()
                flash(
                    f"{SUBJECTS[subjectCode]} subject asigned to {className}", "success")
                return redirect("/bsubjects")


@app.route("/offer_bsubjects", methods=["GET", "POST"])
@login_required
def offer_bsubjects():
    """ List of students for subject registration """
    db_connect = storage()
    with db_connect.cursor() as db_curs:
        if request.method == "POST":
            classid_subjtname = request.form.get("classid_subjtname")
            userid = session['user_id']
            # Split input data
            classID = request.form.get("classid_subjtname").rsplit(",", 1)[0]
            subjectName = request.form.get(
                "classid_subjtname").rsplit(",", 1)[1]
            # Ensure subject is selected
            if classid_subjtname == None:
                flash("Please select subject", "danger")
                return redirect("/offer_bsubjects")
            # Query students in a specified class
            db_curs.execute("""
                            SELECT students.reg_num, ANY_VALUE(surname), ANY_VALUE(othername) FROM people
                            JOIN students ON people.id = students.person_id
                            JOIN classes ON students.class_id = classes.id
                            JOIN teachers ON classes.id = teachers.class_id
                            JOIN class_details ON class_details.currentclass_id = classes.id
                            WHERE teachers.userid = %s AND currentclass_id = %s
                            GROUP BY students.reg_num""", (userid, classID))
            students = db_curs.fetchall()
            db_curs.execute("SELECT * FROM classes")
            classRows = db_curs.fetchall()
            db_curs.execute("""
                            SELECT ANY_VALUE(b_subjects.id), subject_name, ANY_VALUE(subject_code),
                            ANY_VALUE(b_subjects.class_id), class_name
                            FROM b_subjects JOIN classes ON b_subjects.class_id = classes.id
                            JOIN teachers ON b_subjects.teacher_id = teachers.userid
                            GROUP BY subject_name, userid, class_name HAVING userid = %s
                            ORDER BY class_name""", (userid,))
            asignedClassSubjectRows = db_curs.fetchall()
            classCode = ""
            bsubjectId = 0
            subject_code = ""
            # Get classCode, bsubjectId, subject_code from a specified classID
            for asignedClassSubjectRow in asignedClassSubjectRows:
                if asignedClassSubjectRow[1] == subjectName and asignedClassSubjectRow[3] == int(classID):
                    classCode = asign_classcode(
                        asignedClassSubjectRow[4])
                    bsubjectId += asignedClassSubjectRow[0]
                    subject_code += asignedClassSubjectRow[2]
                    break
            # Check if students already registered subject
            REGISTERED_STUDENT_IDS = []
            if asignedClassSubjectRows != None:
                # Asign subject code name
                subjectCodeName = subject_code + classCode
                db_curs.execute("""
                                SELECT * FROM subject_offering WHERE subject_id = %s
                                AND subjectcode_name = %s ORDER BY student_id""",
                                (bsubjectId, subjectCodeName))
                studentIds = db_curs.fetchall()
                if studentIds != None:
                    for studentId in studentIds:
                        REGISTERED_STUDENT_IDS.append(studentId[4])
            # List of subjects asigned to specified class(es)
            ASIGNED_CLASS_SUBJECT_ROWS = []
            for asignedClassSubjectRow in asignedClassSubjectRows:
                ASIGNED_CLASS_SUBJECT_ROWS.append(asignedClassSubjectRow)
            # To dynamically change URL of action attribute on form
            url = "register_bsubjects"
            return render_template("/registerbsubjects.html",
                                   students=students, registeredstudentids=REGISTERED_STUDENT_IDS,
                                   asigned_class_subjects=ASIGNED_CLASS_SUBJECT_ROWS, subject_name=subjectName,
                                   class_id=classID, url=url)

        userid = session["user_id"]
        db_curs.execute("""
                        SELECT subject_name, ANY_VALUE(b_subjects.class_id), class_name FROM b_subjects
                        JOIN classes ON b_subjects.class_id = classes.id
                        JOIN teachers ON b_subjects.teacher_id = teachers.userid
                        GROUP BY subject_name, userid, class_name HAVING userid = %s
                        ORDER BY class_name""", (userid,))
        asignedClassSubjectRows = db_curs.fetchall()
        # List of subjects asigned to specified class(es)
        ASIGNED_CLASS_SUBJECT_ROWS = []
        for asignedClassSubjectRow in asignedClassSubjectRows:
            ASIGNED_CLASS_SUBJECT_ROWS.append(asignedClassSubjectRow)
        # To dynamically change URL of action attribute on form
        url = "offer_bsubjects"
        # To temporary hide student registering form in HTML
        # temp_hide_form = "tdisplay"
        return render_template("/registerbsubjects.html",
                               url=url, asigned_class_subjects=ASIGNED_CLASS_SUBJECT_ROWS)


@app.route("/register_bsubjects", methods=["GET", "POST"])
@login_required
def register_bsubjects():
    """ Register students for a class subject """

    if request.method == "POST":
        db_connect = storage()
        with db_connect.cursor() as db_curs:
            classID = request.form.get("class_id")
            subject_name = request.form.get("subject_name")
            checkedStudentIDs = request.form.getlist("reg_num")
            # Ensure checkbox(es) is/are checked
            if len(checkedStudentIDs) == 0:
                flash("Ensure checkboxe(s) is/are checked", "danger")
                return redirect("/offer_bsubjects")
            # Asign scool session
            schoolSession = school_session()
            userid = session["user_id"]
            db_curs.execute("""
                            SELECT ANY_VALUE(b_subjects.id), subject_name, ANY_VALUE(subject_code) FROM b_subjects
                            JOIN classes ON b_subjects.class_id = classes.id
                            JOIN teachers ON classes.id = teachers.class_id
                            JOIN class_details ON classes.id = class_details.currentclass_id
                            WHERE teachers.userid = %s AND subject_name = %s
                            AND class_details.currentclass_id = %s
                            GROUP BY subject_name, class_details.currentclass_id""",
                            (userid, subject_name, classID))
            bsubjectRow = db_curs.fetchone()
            # Query class asigned to teacher
            db_curs.execute("""
                            SELECT * FROM classes
                            WHERE id = (SELECT class_id FROM teachers WHERE userid = %s
                            AND class_id = %s)""", (userid, classID))
            classRow = db_curs.fetchone()
            # Asign subject code name
            classCode = asign_classcode(classRow[1])
            subjectCodeName = bsubjectRow[2] + classCode
            subject_id = bsubjectRow[0]
            # Register each students for the subject
            for checkedStudentID in checkedStudentIDs:
                db_curs.execute("""
                                INSERT INTO subject_offering (subjectcode_name, sch_session, subject_id, student_id)
                                VALUES(%s, %s, %s, %s)""",
                                (subjectCodeName, schoolSession, subject_id, checkedStudentID))
            db_connect.commit()
            flash(
                f"All checked {classRow[1]} student(s) have been registered for {bsubjectRow[1]} subject", "success")
            return redirect("/offer_bsubjects")


@app.route("/uploadimg/<int:reg_num>", methods=["GET", "POST"])
@login_required
def uploadimg(reg_num):
    """ Upload an image """

    if request.method == "POST":
        # To access a file being posted by a form, use request.files provided by the request object.
        if request.files:
            image = request.files["image"]
            # if file is empty, use default image
            if image.filename == "":
                flash("default image will be use", "success")
                return render_template("/guardians.html", regnum_id=reg_num)
            # Validate the image filesize:
            if not allowed_image_filesize(request.cookies["filesize"]):
                flash("Filesize exceeded expectation", "danger")
                return render_template("/uploadimg.html", reg_num=reg_num)
            # Validating image file extension:
            if allowed_image(image.filename):
                # Ensuring the filename itself isn't dangerous
                filename = secure_filename(image.filename)

                db_connect = storage()
                with db_connect.cursor() as db_curs:
                    # Ensure student exist
                    db_curs.execute(
                        "SELECT * FROM students WHERE reg_num = %s", (reg_num,))
                    student = db_curs.fetchone()

                    print(f'\nstudent: {student}\n')

                    if student == None:
                        flash("Registration number no match", "danger")
                        return redirect("/studentdetails")
                    # with open(image, 'rb') as f:
                    #     binaryimg= f.read()
                        # Add fields to images table
                    db_curs.execute("INSERT INTO images (regnum_id, image, mimetype) VALUES(%s, %s, %s)",
                                    (reg_num, image.read(), image.mimetype))
                    db_connect.commit()

                    print(f'\nImage saved\n')

                    flash("Image saved", "success")
                    return render_template("/guardians.html", regnum_id=reg_num)
            else:
                flash("Only JPEG, JPG, PNG, GIF image extension is allowed", "danger")
                return render_template("uploadimg.html", reg_num=reg_num)
                # return redirect(request.url)
    return render_template("/uploadimg.html")


@app.route("/studentdetails", methods=["GET", "POST"])
@login_required
def studentdetails():

    userid = session['user_id']
    db_connect = storage()
    db_curs = db_connect.cursor()
    if request.method == "POST":
        missing = list()
        # Ensure field(s) was submitted (key : value):
        for k, v in request.form.items():
            if not v:
                missing.append(k)
        if missing:
            flash(f"Missing fields for {', '.join(missing)}", "danger")
            return render_template("studentdetails.html")

        className = request.form.get("classname")
        schoolSession = request.form.get("sch_session")
        admsnDate = datetime.strptime(
            request.form.get("admsn_date"), "%Y-%m-%d")
        st_email = request.form.get("st_email").strip()
        # In format yyyy-mm-dd
        date_of_birth = datetime.strptime(
            request.form.get("date_of_birth"), "%Y-%m-%d")
        gender = request.form.get("gender").capitalize().strip()
        religion = request.form.get("religion").capitalize().strip()
        affiliation = "student"
        surname = request.form.get("surname").capitalize().strip()

        othername = ""
        lga = ""
        state = ""
        nationality = ""
        s_othername = request.form.get("othername").rsplit()
        for i in s_othername:
            othername += f"{i.capitalize()} "
        s_lga = request.form.get("lga").rsplit()
        for i in s_lga:
            lga += f"{i.capitalize()} "
        s_state = request.form.get("state").rsplit()
        for i in s_state:
            state += f"{i.capitalize()} "
        s_nationality = request.form.get("nationality").rsplit()
        for i in s_nationality:
            nationality += f"{i.capitalize()} "

        if className == None:
            flash("Please select class name", "danger")
            return render_template("classdetails.html", classnames=CLASSNAMES, reg_num=reg_num)
        if schoolSession == None:
            flash("Please select session", "danger")
            return render_template("classdetails.html", classnames=CLASSNAMES, reg_num=reg_num)
        # Ensure that class name exist
        if className not in CLASSNAMES:
            return e_message("Invalid Class Name", 404)
        if schoolSession != school_session():
            return e_message("Invalid School Session", 404)

        # Validate the email address and raise an error if it is invalid
        if not email_address_valid(st_email):
            flash("Please enter a valid email address", "danger")
            return render_template("studentdetails.html")

        # Asign registration number
        db_curs.execute("SELECT reg_code FROM unique_ids")
        reg_rows = db_curs.fetchall()

        print(f'\nreg_rows: {reg_rows}\n')

        reg_codes = reg_pool(reg_rows)

        print(f'\nreg_codes: {reg_codes}\n')
        # Ensure registration number is asigned
        if reg_codes == None:
            flash("Couldn't asign registration number", "danger")
            return render_template("studentdetails.html")

        db_curs.execute(
            "SELECT * FROM classes WHERE class_name = %s", (className,))
        classRow = db_curs.fetchone()

        print(f'\nclassRow: {classRow}\n')

        class_id = classRow[0]
        currentclass_id = class_id
        cl_session = schoolSession
        # Check that student is registered and asigned to class not more than ones
        db_curs.execute("""
                        SELECT surname, othername FROM people JOIN students ON  people.id = students.person_id
                        JOIN classes ON students.class_id = classes.id
                        JOIN teachers ON classes.id = teachers.class_id
                        JOIN class_details ON class_details.currentclass_id = classes.id
                        WHERE teachers.userid = %s AND classes.id = %s AND currentclass_id = %s
                        AND people.surname = %s AND people.othername = %s AND cl_session = %s""",
                        (userid, class_id, currentclass_id, surname, othername, cl_session))
        detailsRow = db_curs.fetchone()

        print(f'\ndetailsRow: {detailsRow}\n')

        if detailsRow != None:
            # 'surname'
            flash({detailsRow[0]} + " " + detailsRow[0]
                  ['othername'] + " registered already ", "danger")
            return render_template("studentdetails.html")

        # Register and asign class to student
        db_curs.execute("""
                        INSERT INTO people
                        (surname, othername, gender, lga, states, nationality, religion, date_of_birth, affiliation)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                        (surname, othername, gender, lga, state, nationality, religion, date_of_birth, affiliation))
        db_curs.execute("SELECT LAST_INSERT_ID()")
        peoplePK = db_curs.fetchone()[0]

        reg_num = int(reg_codes["reg_num"])
        # class_id = classRow["id"]
        db_curs.execute("""
                        INSERT INTO students (reg_num, person_id, class_id, st_email)
                        VALUES(%s, %s, %s, %s)""", (reg_num, peoplePK, class_id, st_email))
        # studentPK = db_curs.execute("SELECT LAST_INSERT_ID()")[0]

        year_code = reg_codes["year_code"]
        sch_code = reg_codes["sch_code"]
        reg_code = reg_codes["reg_code"]
        regnum_id = int(reg_codes["reg_num"])

        entryclass_id = class_id
        currentclass_id = class_id
        db_curs.execute("""
                        INSERT INTO unique_ids (year_code, sch_code, reg_code, regnum_id)
                        VALUES(%s, %s, %s, %s)""", (year_code, sch_code, reg_code, regnum_id))
        db_curs.execute("""
                        INSERT INTO class_details (entryclass_id, currentclass_id, admsn_date, cl_session)
                        VALUES(%s, %s, %s, %s)""", (entryclass_id, currentclass_id, admsnDate, schoolSession))
        db_connect.commit()
        db_curs.close()
        db_connect.close()

        reg_num = int(reg_codes["reg_num"])
        flash("Details saved", "success")
        return render_template("/uploadimg.html", reg_num=reg_num)

    # if request.method is GET
    schoolSession = school_session()
    db_curs.execute("""
                    SELECT class_name FROM classes WHERE id IN
                    (SELECT class_id FROM teachers WHERE userid = %s)
                    ORDER BY class_name""", (userid,))
    classNames = db_curs.fetchall()
    db_curs.close()
    db_connect.close()
    return render_template("/studentdetails.html", classnames=classNames, schoolsession=schoolSession)


@app.route("/guardians/<int:regnum_id>", methods=["GET", "POST"])
@login_required
def guardians(regnum_id):

    if request.method == "POST":
        missing = list()
        # Ensure field(s) was submitted (key : value):
        # -------------------------------------------
        for k, v in request.form.items():
            if not v:
                missing.append(k)
        if missing:
            flash(f"Missing fields for {', '.join(missing)}", "danger")
            return render_template("guardians.html")

        email = request.form.get("g_email").strip()
        phone = request.form.get("g_phone")

        g_address = ""
        address = request.form.get("g_address").rsplit()
        for item in address:
            g_address += f"{item.capitalize()} "
        g_name = ""
        names = request.form.get("g_name").rsplit()
        for name in names:
            g_name += f"{name.capitalize()} "
        db_connect = storage()
        with db_connect.cursor() as db_curs:
            db_curs.execute("""
                    INSERT INTO guardians (regnum_id, g_name, g_address, g_email, g_phone)
                    VALUES(%s, %s, %s, %s, %s)""",
                            (regnum_id, g_name.strip(), g_address.strip(), email, phone))
            db_connect.commit()
        flash("Guardians details saved", "success")
        return redirect("/")

    return render_template("/guardians.html")


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
        db_connect = storage()
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


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()
    # Redirect user to login form
    return redirect("/")


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
            db_curs.execute(
                "SELECT * FROM users WHERE username = %s", (username,))
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
                    "INSERT INTO users (username, password_hash) VALUES(%s, %s)",
                    (username, hash))
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
