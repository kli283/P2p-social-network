import sqlite3




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
        cursor.execute("UPDATE UserInfo SET Location = ?, IP = ?, PORT = ?, LoginTime = ? where UPI == ?", (user['location'], user['ip'], user['port'], user['lastLogin'], user['username']))
    connection.commit()
    cursor.close()


def add_msg_db(sender, receiver, message, timestamp):
    connection = sqlite3.connect("LiChat.db")
    cursor = connection.cursor()
    # cursor.execute(
    #     "CREATE TABLE IF NOT EXISTS Messages(Sender TEXT, Receiver TEXT, Message TEXT, Timestamp INTEGER)")
    tupleData = (sender, receiver, message, timestamp)
    cursor.execute("INSERT INTO Messages (Sender, Receiver, Message, Timestamp) VALUES (?,?,?,?)", tupleData)
    connection.commit()
    cursor.close()

