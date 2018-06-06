import hashlib
import sqlite3

# This function encrypts the string
def encrypt_string(user, pw):
    hash_string = pw + user
    encrypted = hashlib.sha256(hash_string.encode()).hexdigest()
    return encrypted

# This function splits the list of UPIs provided by the login server
def split_upi(upis):
    upiList = [x.strip() for x in upis.split(',')]
    return upiList


