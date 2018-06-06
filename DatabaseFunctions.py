import sqlite3


# This function initialises the database, creating all the necessary tables
def create_database():
    connection = sqlite3.connect("LiChat.db")
    cursor = connection.cursor()
    try:
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS Messages(MessageID INTEGER PRIMARY KEY, Sender TEXT, Receiver TEXT, Message TEXT, Timestamp INTEGER, content_type TEXT)")
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS Profiles(ProfileID INTEGER PRIMARY KEY, UPI TEXT UNIQUE, fullname TEXT,position TEXT, description TEXT, location TEXT, picture TEXT, lastUpdated TEXT)")
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS UserInfo(UPI TEXT UNIQUE, Location TEXT, IP TEXT, PORT TEXT, LoginTime TEXT)")
    except:
        print("Error initialising database")
    connection.commit()
    cursor.close()


# This function initialises the table for the active users
def init_current_user():
    connection = sqlite3.connect("LiChat.db")
    cursor = connection.cursor()
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS UserCredentials(UserID INTEGER PRIMARY KEY, UPI TEXT UNIQUE, PW TEXT, Location INTEGER)")


# This function adds the newly logged on user to the table
def add_current_user(username, password, location):
    connection = sqlite3.connect("LiChat.db")
    cursor = connection.cursor()
    tupleData = (username, password, location)
    cursor.execute("INSERT OR REPLACE INTO UserCredentials (UPI, PW, Location) VALUES (?,?,?)", tupleData)
    connection.commit()
    cursor.close()


# This is a getter function for the logged on user
def get_current_user():
    connection = sqlite3.connect("LiChat.db")
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT * FROM UserCredentials")
    except:
        print("-----No user in DB-----")
    userCred = cursor.fetchall()
    connection.commit()
    cursor.close()
    return userCred


# This function drops the table from the database making sure no details are accidentally still stored on the database
def drop_current():
    connection = sqlite3.connect("LiChat.db")
    cursor = connection.cursor()
    try:
        cursor.execute("DROP TABLE UserCredentials")
    except:
        pass
    connection.commit()
    cursor.close()


# This function drops a logged in user from the database
def drop_current_user(user):
    connection = sqlite3.connect("LiChat.db")
    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM UserCredentials WHERE UPI == ?", user)
    except:
        pass
    connection.commit()
    cursor.close()


# This function adds all the UPIs passed into it to the database
def add_upi_db(userList):
    connection = sqlite3.connect("LiChat.db")
    cursor = connection.cursor()
    for upi in userList:
        cursor.execute("INSERT OR REPLACE INTO UserInfo (UPI) VALUES (?)", (upi,))
        connection.commit()
    cursor.close()


# This function adds all the users details into the database
def add_online_db(userDictionary):
    connection = sqlite3.connect("LiChat.db")
    cursor = connection.cursor()
    userDictionary = userDictionary.values()
    # Data is stored while being organised
    for user in userDictionary:
        cursor.execute(
            "UPDATE UserInfo SET Location = ?, IP = ?, PORT = ?, LoginTime = ? WHERE UPI == ?", (
                user['location'], user['ip'], user['port'],
                float(user['lastLogin']), user['username']))
    connection.commit()
    cursor.close()


# This function adds all the details within the message to the database
def add_msg_db(sender, receiver, message, timestamp):
    connection = sqlite3.connect("LiChat.db")
    cursor = connection.cursor()
    tupleData = (sender, receiver, message, timestamp)
    cursor.execute("INSERT OR IGNORE INTO Messages (Sender, Receiver, Message, Timestamp) VALUES (?,?,?,?)", tupleData)
    connection.commit()
    cursor.close()

# This is a getter function for the message specific to the username that is being passed in
def get_msg(username):
    connection = sqlite3.connect("LiChat.db")
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Messages")
    connection.commit()
    msg = cursor.fetchall()
    returnMsg = []
    for row in msg:
        if row[1] == username or row[2] == username:
            returnMsg.append(row)
    connection.commit()
    cursor.close()
    return returnMsg


# This is a getter function for messages specific to the sender and receiver that are being passed in
def get_convo(sender, receiver):
    connection = sqlite3.connect("LiChat.db")
    cursor = connection.cursor()
    cursor.execute(
        "SELECT * FROM Messages WHERE (Sender = (?) AND Receiver = (?)) OR (Sender = (?) AND Receiver = (?))",
        (sender, receiver, receiver, sender))
    connection.commit()
    msg = cursor.fetchall()
    return msg


# This function adds the profile details into the database in an organised way
def add_profile(UPI, name, position, description, location, picture, timestamp):
    connection = sqlite3.connect("LiChat.db")
    cursor = connection.cursor()
    tupleData = (UPI, name, position, description, location, picture, timestamp)
    cursor.execute(
        "INSERT OR REPLACE INTO Profiles (UPI, fullname, position, description, location, picture, lastUpdated) VALUES (?,?,?,?,?,?,?)",
        tupleData)
    connection.commit()
    cursor.close()


# This is a getter function to get the profile specific to the UPI being passed through
def get_user_profile(UPI):
    connection = sqlite3.connect("LiChat.db")
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Profiles WHERE UPI = (?)", (UPI,))
    connection.commit()
    profile = cursor.fetchall()
    connection.close()
    return profile


# This is a getter function to get the IP of the specific UPI being passed through
def get_ip(UPI):
    connection = sqlite3.connect("LiChat.db")
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT IP FROM UserInfo WHERE UPI = (?)", (UPI,))
        ip = cursor.fetchone()[0]
        return ip
    except:
        print("Error finding IP")
        pass
    connection.commit()
    connection.close()


# This is a getter function to get the port of the specific UPI being passed through
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
