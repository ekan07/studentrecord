#!/usr/bin/python3
# from flask import Flask, render_template, request
# prompts for hiden password
from getpass import getpass
import os

# from studentrecord import app


def dbstorage():
    """
    """
    # Module For Connecting To MySQL database
    import MySQLdb
    import sys

    # dialect = "mysql"
    # driver = "mysqldb"
    # port = 3306
    # user = os.getenv("ALX_MYSQL_USER")
    # passwd = os.getenv("ALX_MYSQL_PWD")
    # host = os.getenv("ALX_MYSQL_HOST")
    # db_name = os.getenv("ALX_MYSQL_DB")


    # Trying to connect
    # try:
    # db_connect = MySQLdb.connect(host='localhost', port=3306,
    #                                 user='root', passwd=sys.argv[3], db='studentrecord')
    # db_connection = MySQLdb.connect
    # ("localhost", "root", "", "studentrecord")
    db_connect = MySQLdb.connect(host='localhost',
                                 user=os.environ.get('PORTFOLIO_USER'),
                                 passwd=os.environ.get('PORTFOLIO_PWD'),
                                 db='studentrecord')
    # If connection is not successful
    # except:
    # print("Can't connect to database")
    # return 0
    # If Connection Is Successful
    # print("Connected")

    # Making Cursor Object For Query Execution
    # db_curs = db_connect.cursor()
    # Executing Query
    # cur.execute("SELECT CURDATE();")
    # Above Query Gives Us The Current Date
    # Fetching Data
    # m = cur.fetchone()

    # Printing Result Of Above
    # print("Today's Date Is ", m[0])
    # Closing Database Connection
    # db_connect.close()
    return db_connect


# Function Call For Connecting To Our Database
# mysqlconnect()


# app.config['MYSQL_HOST'] = 'localhost'
# app.config['MYSQL_USER'] = 'root'
# app.config['MYSQL_PASSWORD'] = 'stand07stone'
# app.config['MYSQL_DB'] = 'studentrecord'

# mysql = MySQL(app)
# # Creating a connection cursor
# cursor = mysql.connection.cursor()
