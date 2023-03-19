#!/usr/bin/python3
# from flask import Flask, render_template, request
import os

# from studentrecord import app


def mysqlconnect():
    """"""
    # Module For Connecting To MySQL database
    import MySQLdb
    import sys


    # Trying to connect
    # try:
    # db_connection = MySQLdb.connect(host='localhost', port=3306,
    #                                 user=sys.argv[1], passwd=sys.argv[2], db=sys.argv[3])
    # db_connection = MySQLdb.connect
    # ("localhost", "root", "stand07stone", "studentrecord")
    db_connect = MySQLdb.connect(host='localhost',
                                 user='root', passwd='stand07stone', db='studentrecord')
    # If connection is not successful
    # except:
    # print("Can't connect to database")
    # return 0
    # If Connection Is Successful
    # print("Connected")

    # Making Cursor Object For Query Execution
    curs = db_connect.cursor()

    # Executing Query
    # cur.execute("SELECT CURDATE();")
    # Above Query Gives Us The Current Date
    # Fetching Data
    # m = cur.fetchone()

    # Printing Result Of Above
    # print("Today's Date Is ", m[0])
    # Closing Database Connection
    # db_connect.close()
    return curs, db_connect


# Function Call For Connecting To Our Database
# mysqlconnect()


# def mysqlconnect():
#     # Trying to connect
#     db_connection = None
#     try:
#         db_connection = MySQLdb.connect(
#             dcfg.mysql["host"],
#             dcfg.mysql["user"],
#             dcfg.mysql["password"],
#             dcfg.mysql["db"],
#             dcfg.mysql["port"]
#         )
#     # If connection is not successful
#     except:
#         print("Can't connect to database")
#         return 0
#     # If Connection Is Successful
#     print("Connected")

#     # Making Cursor Object For Query Execution
#     cursor = db_connection.cursor()


# class DBStorage:
#     """
#     """

#     def __init__(self):
#         """
#         """
#         app.config['MYSQL_HOST'] = 'localhost'
#         app.config['MYSQL_USER'] = 'root'
#         app.config['MYSQL_PASSWORD'] = 'stand07stone'
#         app.config['MYSQL_DB'] = 'studentrecord'

#         mysql = MySQL(app)
#         # Creating a connection cursor
#         cursor = mysql.connection.cursor()
