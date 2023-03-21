-- "localhost", "alxmysqlpwd", "alxmysqlpwd", "studentrecord"
CREATE USER IF NOT EXISTS `alxmysquser`@`localhost` IDENTIFIED BY 'alxmysqlpwd';

CREATE DATABASE IF NOT EXISTS studentrecord;

GRANT ALL PRIVILEGES ON `studentrecord`.* TO `alxmysquser`@`localhost`;

USE studentrecord;

CREATE TABLE IF NOT EXISTS users (
    id INT UNIQUE NOT NULL AUTO_INCREMENT,
    username VARCHAR(256) NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    PRIMARY KEY(id));

CREATE TABLE IF NOT EXISTS people (
    id INT UNIQUE NOT NULL AUTO_INCREMENT,
    surname VARCHAR(256) NOT NULL,
    othername VARCHAR(256) NOT NULL,
    gender VARCHAR(256) NOT NULL, 
    lga VARCHAR(256) NOT NULL,
    states VARCHAR(256) NOT NULL,
    nationality VARCHAR(256) NOT NULL,
    religion VARCHAR(256) NOT NULL, 
    date_of_birth VARCHAR(256) NOT NULL,
    affiliation VARCHAR(256) NOT NULL,
    PRIMARY KEY(id));

CREATE TABLE IF NOT EXISTS teachers (
     id INT UNIQUE NOT NULL AUTO_INCREMENT,
     person_id INT,
     class_id INT NOT NULL,
     userid INT NOT NULL,
     FOREIGN KEY(person_id) REFERENCES people(id), 
     FOREIGN KEY(class_id) REFERENCES classes(id),
     FOREIGN KEY(userid) REFERENCES users(id), PRIMARY KEY(id));

CREATE TABLE IF NOT EXISTS b_subjects (
    id INT UNIQUE NOT NULL AUTO_INCREMENT,
    subject_name VARCHAR(256) NOT NULL,
    subject_code VARCHAR(256) NOT NULL,
    teacher_id INT NOT NULL, 
    class_id INT NOT NULL,
    FOREIGN KEY(teacher_id) REFERENCES users(id),
    FOREIGN KEY(class_id) REFERENCES classes(id), 
    PRIMARY KEY(id));

CREATE TABLE IF NOT EXISTS subject_offering (
    id INT UNIQUE NOT NULL AUTO_INCREMENT,
    subjectcode_name VARCHAR(256) NOT NULL,
    sch_session VARCHAR(256) NOT NULL,
    subject_id INT NOT NULL,
    student_id INT NOT NULL,
    FOREIGN KEY(subject_id) REFERENCES b_subjects(id), 
    FOREIGN KEY(student_id) REFERENCES students(reg_num), PRIMARY KEY(id));

CREATE TABLE IF NOT EXISTS classes (
    id INT UNIQUE NOT NULL AUTO_INCREMENT,
    class_name VARCHAR(256) NOT NULL,
    PRIMARY KEY(id));

CREATE TABLE IF NOT EXISTS class_details (
    id INT UNIQUE NOT NULL AUTO_INCREMENT,
    entryclass_id INT NOT NULL,
    currentclass_id INT NOT NULL,
    admsn_date VARCHAR(256) NOT NULL, 
    cl_session VARCHAR(256) NOT NULL,
    class_status VARCHAR(256) DEFAULT 'Active',
    trans_grad_date VARCHAR(256) DEFAULT 'Not applicable',
    FOREIGN KEY(currentclass_id) REFERENCES classes(id),
    PRIMARY KEY(id));

CREATE TABLE IF NOT EXISTS students (
    id INT UNIQUE NOT NULL AUTO_INCREMENT,
    reg_num INT UNIQUE,
    person_id INT,
    class_id INT NOT NULL,
    st_email VARCHAR(256) NOT NULL,
    FOREIGN KEY(person_id) REFERENCES people(id),
    FOREIGN KEY(class_id) REFERENCES classes(id),
    PRIMARY KEY(id));

CREATE TABLE IF NOT EXISTS images (
    id INT UNIQUE NOT NULL AUTO_INCREMENT,
    regnum_id INT NOT NULL,
    image VARCHAR(256) NOT NULL,
    mimetype VARCHAR(256) NOT NULL,
    FOREIGN KEY(regnum_id) REFERENCES students(id),
    PRIMARY KEY(id));

CREATE TABLE IF NOT EXISTS unique_ids (
    id INT UNIQUE NOT NULL AUTO_INCREMENT,
    year_code VARCHAR(256) NOT NULL,
    sch_code VARCHAR(256) NOT NULL,
    reg_code INT NOT NULL, 
    regnum_id INT NOT NULL,
    FOREIGN KEY(regnum_id) REFERENCES students(reg_num),
    PRIMARY KEY(id));

CREATE TABLE IF NOT EXISTS guardians (
    id INT UNIQUE NOT NULL AUTO_INCREMENT,
    regnum_id INT NOT NULL,
    g_name VARCHAR(256) NOT NULL,
    g_address VARCHAR(256) NOT NULL,
    g_email VARCHAR(256) NOT NULL,
    g_phone VARCHAR(256) NOT NULL, 
    FOREIGN KEY(regnum_id) REFERENCES students(id),
    PRIMARY KEY(id));


SHOW DATABASES;