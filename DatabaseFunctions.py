import sqlite3
import time


def add_upi_db(userList):
    # cursor.execute("CREATE TABLE IF NOT EXISTS UserInfo(UPI TEXT, Location INTEGER, IP INTEGER, PORT INTEGER, LoginTime INTEGER)")
    connection = sqlite3.connect("LiChat.db")
    cursor = connection.cursor()

    for upi in userList:
        cursor.execute("INSERT INTO UserInfo (UPI) VALUES (?)", (upi,))
        connection.commit()
    cursor.close()


# def add_online_db(UPI, location, IP, port, timestamp):
#     # cursor.execute("CREATE TABLE IF NOT EXISTS UserInfo(UPI TEXT, Location INTEGER, IP INTEGER, PORT INTEGER, LoginTime INTEGER)")
#     connection = sqlite3.connect("LiChat.db")
#     cursor = connection.cursor()
#
#     tupleData = (location, IP, port, timestamp, UPI)
#     cursor.execute("UPDATE UserInfo SET Location = ?, IP = ?, PORT = ?, LoginTime = ? where UPI == ?", tupleData)
#     connection.commit()
#     cursor.close()


def add_online_db(userDictionary):
    # cursor.execute("CREATE TABLE IF NOT EXISTS UserInfo(UPI TEXT, Location INTEGER, IP INTEGER, PORT INTEGER, LoginTime INTEGER)")
    connection = sqlite3.connect("LiChat.db")
    cursor = connection.cursor()
    userDictionary = userDictionary.values()
    # tupleData = (location, IP, port, timestamp, UPI)


    for user in userDictionary:
        cursor.execute("UPDATE UserInfo SET Location = ?, IP = ?, PORT = ?, LoginTime = ?, isOnline = '1' WHERE UPI == ?", (
        user['location'], user['ip'], user['port'],
        time.strftime("%d-%m-%Y %I:%M %p", time.localtime(float(user['lastLogin']))), user['username']))
    # users = cursor.fetchone()[0]
    connection.commit()
    cursor.close()
    # return users


# def add_online_db(userDictionary):
#     # cursor.execute("CREATE TABLE IF NOT EXISTS UserInfo(UPI TEXT, Location INTEGER, IP INTEGER, PORT INTEGER, LoginTime INTEGER)")
#     connection = sqlite3.connect("LiChat.db")
#     cursor = connection.cursor()
#     userDictionary = userDictionary.values()
#     # tupleData = (location, IP, port, timestamp, UPI)
#     for user in userDictionary:
#         cursor.execute("UPDATE UserInfo SET Location = ?, IP = ?, PORT = ?, LoginTime = ?, isOnline = '1' WHERE UPI == ?", (
#         user['location'], user['ip'], user['port'],
#         time.strftime("%d-%m-%Y %I:%M %p", time.localtime(float(user['lastLogin']))), user['username']))
#     connection.commit()
#     cursor.close()


# def set_online(user):
#     connection = sqlite3.connect("LiChat.db")
#     cursor = connection.cursor()
#     if (user == ):
#         cursor.execute("UPDATE UserInfo SET isOnline = '1'")
#     else:
#         cursor.execute("UPDATE UserInfo SET isOnline = '0'")
#     connection.commit()
#     cursor.close()
#
def get_online():
    connection = sqlite3.connect("LiChat.db")
    cursor = connection.cursor()

    cursor.execute("SELECT UPI FROM UserInfo WHERE isOnline = '1'")


def add_msg_db(sender, receiver, message, timestamp):
    connection = sqlite3.connect("LiChat.db")
    cursor = connection.cursor()
    # cursor.execute(
    #     "CREATE TABLE IF NOT EXISTS Messages(Sender TEXT, Receiver TEXT, Message TEXT, Timestamp INTEGER)")
    tupleData = (sender, receiver, message, timestamp)
    cursor.execute("INSERT INTO Messages (Sender, Receiver, Message, Timestamp) VALUES (?,?,?,?)", tupleData)
    connection.commit()
    cursor.close()


def add_profile(name, position, description, location, picture, timestamp):
    connection = sqlite3.connect("LiChat.db")
    cursor = connection.cursor()
    tupleData = (name, position, description, location, picture, timestamp)
    cursor.execute("INSERT or REPLACE INTO Messages (fullname, position, description, location, picture, lastUpdated) VALUES (?,?,?,?,?,?)", tupleData)
    connection.commit()
    cursor.close()


def get_ip(UPI):
    connection = sqlite3.connect("LiChat.db")
    cursor = connection.cursor()
    cursor.execute("SELECT IP FROM UserInfo WHERE UPI = (?)", (UPI,))
    ip = cursor.fetchone()[0]
    return ip


def get_port(UPI):
    connection = sqlite3.connect("LiChat.db")
    cursor = connection.cursor()
    cursor.execute("SELECT PORT FROM UserInfo WHERE UPI = (?)", (UPI,))
    port = cursor.fetchone()[0]
    return port
