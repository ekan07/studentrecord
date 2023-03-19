# from engine import db_storage

# storage = db_storage.mysqlconnect


# def register_page():
#     try:
#         curs, db_connect = storage()
#         # Executing Query
#         curs.execute("SELECT CURDATE();")
#         # Above Query Gives Us The Current Date
#         # Fetching Data
#         m = curs.fetchone()

#         # Printing Result Of Above
#         print("Today's Date Is ", m[0])
#         # Closing Database Connection
#         db_connect.close()
#         return("okay")
#     except:
#         print("Can't connect to database")
#         return 0


# register_page()
