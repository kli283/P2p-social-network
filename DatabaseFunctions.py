import sqlite3
import time


def init_current_user():
    connection = sqlite3.connect("LiChat.db")
    cursor = connection.cursor()
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS UserCredentials(UserID INTEGER PRIMARY KEY, UPI TEXT UNIQUE, PW TEXT, Location INTEGER)")


def add_current_user(username, password, location):
    connection = sqlite3.connect("LiChat.db")
    cursor = connection.cursor()
    tupleData = (username, password, location)
    cursor.execute("INSERT OR REPLACE INTO UserCredentials (UPI, PW, Location) VALUES (?,?,?)", tupleData)
    connection.commit()
    cursor.close()


def get_current_user():
    connection = sqlite3.connect("LiChat.db")
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT * FROM UserCredentials")
    except:
        print("No user in DB")
    userCred = cursor.fetchall()
    connection.commit()
    cursor.close()
    return userCred


def drop_current():
    connection = sqlite3.connect("LiChat.db")
    cursor = connection.cursor()
    try:
        cursor.execute("DROP TABLE UserCredentials")
    except:
        pass
    connection.commit()
    cursor.close()

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
        cursor.execute(
            "UPDATE UserInfo SET Location = ?, IP = ?, PORT = ?, LoginTime = ?, isOnline = '1' WHERE UPI == ?", (
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
    # try:
    cursor.execute("INSERT INTO Messages (Sender, Receiver, Message, Timestamp) VALUES (?,?,?,?)", tupleData)
    # except:
    #     pass
    connection.commit()
    cursor.close()


def get_msg(username):
    connection = sqlite3.connect("LiChat.db")
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Messages")
    connection.commit()
    msg = cursor.fetchall()
    returnMsg = []
    for row in msg:
        if (row[1] == username or row[2] == username):
            returnMsg.append(row)
    connection.commit()
    cursor.close()
    return returnMsg

def get_convo(sender, receiver):
    connection = sqlite3.connect("LiChat.db")
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Messages WHERE (Sender = (?) AND Receiver = (?)) OR (Sender = (?) AND Receiver = (?))", (sender, receiver, receiver, sender))
    connection.commit()
    msg = cursor.fetchall()
    print(msg)
    return msg


def add_profile(UPI, name, position, description, location, picture, timestamp):
    connection = sqlite3.connect("LiChat.db")
    cursor = connection.cursor()
    tupleData = (UPI, name, position, description, location, picture, timestamp)
    cursor.execute(
        "INSERT OR REPLACE INTO Profiles (UPI, fullname, position, description, location, picture, lastUpdated) VALUES (?,?,?,?,?,?,?)",
        tupleData)
    connection.commit()
    cursor.close()


def get_user_profile(UPI):
    connection = sqlite3.connect("LiChat.db")
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Profiles WHERE UPI = (?)", (UPI,))
    connection.commit()
    profile = cursor.fetchall()
    print profile
    connection.close()
    return profile


def get_ip(UPI):
    connection = sqlite3.connect("LiChat.db")
    cursor = connection.cursor()
    cursor.execute("SELECT IP FROM UserInfo WHERE UPI = (?)", (UPI,))
    ip = cursor.fetchone()[0]
    connection.commit()
    connection.close()
    return ip


def get_port(UPI):
    connection = sqlite3.connect("LiChat.db")
    cursor = connection.cursor()
    cursor.execute("SELECT PORT FROM UserInfo WHERE UPI = (?)", (UPI,))
    port = cursor.fetchone()[0]
    connection.commit()
    connection.close()
    return port


def add_file_db(sender, destination, filename, stamp, content_type):
    connection = sqlite3.connect("LiChat.db")
    cursor = connection.cursor()
    tupleData = (sender, destination, filename, stamp, content_type)
    cursor.execute("INSERT INTO Messages (Sender, Receiver, Message, Timestamp, content_type) VALUES (?,?,?,?,?)",
                   tupleData)
    connection.commit()
    connection.close()
