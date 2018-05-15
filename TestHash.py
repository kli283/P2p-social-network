import hashlib
import requests


def encrypt_string(user, pw):
    hash_string = pw + user
    encrypted = hashlib.sha256(hash_string.encode()).hexdigest()
    return encrypted


username = raw_input("Enter username: ")
password = raw_input("Enter password: ")

userData = {'username': username, 'password': encrypt_string(username, password), 'location': '2', 'ip': '172.23.128.162', 'port': '10001'}
r = requests.get('http://cs302.pythonanywhere.com/report', params=userData)
code = r.text[0:1]

print(r.url)
print(r.text)
print(code)
#r = requests.post()
# username = "kli283"
# password = "maximumdescent"



#
# import hashlib
#
#
# def encrypt_string(hash_string):
#     sha_signature = \
#         hashlib.sha256(hash_string.encode()).hexdigest()
#     return sha_signature
#
#
# hash_string = 'confidential data'
# sha_signature = encrypt_string(hash_string)
# print(sha_signature)
