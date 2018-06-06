import hashlib
import sqlite3


def encrypt_string(user, pw):
    hash_string = pw + user
    encrypted = hashlib.sha256(hash_string.encode()).hexdigest()
    return encrypted


def split_upi(upis):
    upiList = [x.strip() for x in upis.split(',')]
    return upiList


def get_user_list():
    connection = sqlite3.connect("LiChat.db")
    cursor = connection.cursor()
    cursor.execute("SELECT UPI FROM UserInfo")
    data = cursor.fetchall()
    return data
