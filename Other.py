#!/usr/bin/python
""" cherrypy_example.py

    COMPSYS302 - Software Design
    Author: Andrew Chen (andrew.chen@auckland.ac.nz)
    Last Edited: 19/02/2015

    This program uses the CherryPy web server (from www.cherrypy.org).
"""
# Requires:  CherryPy 3.2.2  (ww#FF0909#000000w.cherrypy.org)
#            Python  (We use 2.7)

import socket

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(('8.8.8.8', 80))
listen_ip = s.getsockname()[
    0]  # get local ip address : Reference "https://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib"
s.close()

# Only ports 10000 - 10005 open on linux
listen_port = 10009

if (listen_ip.startswith('10.103')) or (listen_ip.startswith('10.104')):  # uni labs
    location = str(0)
elif listen_ip.startswith('172.23'):  # uni wifi
    location = str(1)
else:
    location = str(2)

import cherrypy
import sqlite3  # for database
import hashlib  # for encypting data
import sys
import urllib
import urllib2
import time
import json
import requests
import jinja2
import mimetypes
import socket
import threading
import os
import webbrowser
import base64
import dbFunctions  # My function for reading/writing to database
import ReaderFunctions  # Helping reader functions
# import Messages
from urllib2 import Request, URLError, urlopen, HTTPError  # request, error and open
from cherrypy._cpserver import Server  # to run multiple servers
import jinja2

env = jinja2.Environment(
    loader=jinja2.FileSystemLoader('templates'))

global registeredUsers  # creating global list of users
request = Request('http://cs302.pythonanywhere.com/listUsers?')
response = urlopen(request)
registeredUsers = response.read().split(",")

global threadCount
threadCount = 1


class MainApp(object):
    WEB_ROOT = os.getcwd() + '\\static'

    # CherryPy Configuration
    _cp_config = {'tools.encode.on': True,
                  'tools.encode.encoding': 'utf-8',
                  'tools.sessions.on': 'True',
                  'tools.staticdir.debug': 'True',
                  'tools.staticdir.on': 'True',
                  'tools.staticdir.dir': WEB_ROOT,
                  'tools.staticdir.index': 'templates/index.html'
                  }

    # If they try somewhere we don't know, catch it here and send them to the right place.
    @cherrypy.expose
    def default(self, *args, **kwargs):
        """The default page, given when we don't recognise where the request is for."""
        Page = "Invalid: 404 Error."
        cherrypy.response.status = 404
        return Page

    # PAGES (which return HTML that can be viewed in browser)
    @cherrypy.expose
    def index(self):  # Default page that someone goes to when they go to the port
        template = env.get_template('JaedynIndex.html')
        try:
            global registeredUsers
            dbFunctions.updateUserList(registeredUsers)  # update user list with log in server
            dataList = dbFunctions.getAllProfiles()
            dataReplace = {'WelcomeMessage': "Welcome " + cherrypy.session['username'],
                           'UserList': dataList}  # user list
            template = env.get_template('JaedynDashboard.html')
            return template.render(dataReplace)
        except KeyError:  # There is no username
            template = env.get_template('JaedynIndex.html')
            return template.render()

    @cherrypy.expose
    def download(self, fname):
        src = "/Downloads/"
        f = open(fname, 'rb')
        data = f.read()
        f.close()
        return data

    @cherrypy.expose
    def ping(self,
             sender=None):  # allows others to ping and see if you are here. optional for those who dont want to put sender as a paramter

        return str(0)

    @cherrypy.expose
    @cherrypy.tools.json_in()
    def getStatus(self):  # allows others to ping and see if you are here
        data = cherrypy.request.json  # load json object into dictionary
        status = dbFunctions.getUserStatus(data['profile_username'])
        return json.dumps({'status': status[0][0]})

    @cherrypy.expose
    def viewMessages(self):  # Default page that someone goes to when they go to the port
        Page = "Welcome! This is Jaedyns Social Network<br/>"

        try:
            Page = "Hello " + cherrypy.session['username'] + "!<br/>"
            raise cherrypy.HTTPRedirect("/searchProfile?user=" + cherrypy.session.get('username'))
        except KeyError:  # There is no username
            raise cherrypy.HTTPRedirect("/login")  # raise view messages
        return Page

    @cherrypy.expose
    def deleteMessage(self):
        try:
            dbFunctions.deleteMessages(cherrypy.session.get(
                'username'))  # call helper function to delete messages. keeps the database not exposed too
        except KeyError:
            raise cherrypy.HTTPRedirect("/displayProfile")  # raise view messages
        raise cherrypy.HTTPRedirect("/displayProfile")  # raise view messages
        return

    @cherrypy.expose
    def deleteFile(self):
        try:
            dbFunctions.deleteFiles(cherrypy.session.get(
                'username'))  # call helper function to delete messages. keeps the database not exposed too
        except KeyError:
            raise cherrypy.HTTPRedirect("/displayProfile")  # raise view messages
        raise cherrypy.HTTPRedirect("/displayProfile")  # raise view messages
        return

    @cherrypy.expose
    def sendFile(self, fname, destination):
        file = base64.b64encode(fname.file.read())  # base 64 encode data
        filename = str(fname.filename)
        content = mimetypes.guess_type(filename, strict=True)  # guess mimetype
        content_type = content[0]  # get mimetype from tuple
        encoding_tpye = content[1]  # zip etc.
        size = len(file)
        print("size is this!: " + str(size))
        if size > 5000000:
            return "File size greater than 5MB!"
        # self.updateUserSecurity() # Update IP, Port, Location, Public key for all current online users
        dets = dbFunctions.getReceiverDetails(destination)
        try:  # get receiver latest details from database
            IP = dets[0][0]  # IP
            Port = dets[0][1]  # Port
            PublicKey = dets[0][2]  # Public key
            if (IP == None) or (
                    Port == None):  # if no port or IP in database then we cannot send message, maybe show a error message here
                raise cherrypy.HTTPRedirect("/displayProfile")
            ping = self.pingUser(cherrypy.session.get('username'), IP, Port)  # ping receiver see if they're there
            if (ping == "0"):  # user is online so end them a message
                # if (PublicKey != none): # if they have a public key then encrypt with their public key
                # encyrpt message with public key
                now = float(time.mktime(time.localtime()))
                postdata = {'sender': cherrypy.session.get('username'), 'destination': str(destination), 'file': file,
                            'filename': filename, 'content_type': content_type, 'stamp': now, 'encryption': 0,
                            'hashing': 0}  # dictionary to be put into json
                dest = 'http://' + IP + ":" + Port + '/receiveFile'  # BACK UP ABOVE, this LISTEN_IP/PORT should be the recievers IP/PORT instead
                data = json.dumps(postdata)  # turns into json
                req = urllib2.Request(dest, data=data,
                                      headers={'content-type': 'application/json'})  # or json = postdata
                response = urllib2.urlopen(req)  # send user message json dic encoded
                if (response.read() == "0"):
                    dbFunctions.writeFile(cherrypy.session.get('username'), str(destination),
                                          time.strftime("%d-%m-%Y %I:%M %p", time.localtime(now)), str(filename),
                                          str(content_type), file)
                    return
            else:  # implement offline messaging here
                # raise cherrypy.HTTPRedirect("/displayProfile")  #placeholder for offline messaging
                return "USER IS OFFLINE"  # for test
        except IndexError:  # Receiver is not in database
            # raise cherrypy.HTTPRedirect("/displayProfile")
            return "USER IS NOT IN DATABASE"  # for test
        raise cherrypy.HTTPRedirect("/displayProfile")  # after sending is done. redirect back to profile.

    # return "received!" # for test

    @cherrypy.expose
    @cherrypy.tools.json_in()
    def receiveFile(self):  # BACKUP BELOW
        try:
            data = cherrypy.request.json  # load json object into dictionary
            Blacklist = dbFunctions.getBlacklist(cherrypy.session.get('username'))
            for x in Blacklist:
                if data['sender'] == x[2]:  # check if sender is in the local user's blacklist
                    return "11"  # code for black listed
            dbFunctions.writeFile(data['sender'], data['destination'],
                                  time.strftime("%d-%m-%Y %I:%M %p", time.localtime(data['stamp'])), data['filename'],
                                  data['content_type'], data[
                                      'file'])  # Use my database helper to write received message into database. Good because database is not exposed
        except IndexError:
            return "1"  # missing compulsary field
        return "0"  # success

    @cherrypy.expose
    def downloadFile(self, fname, fileData):
        fileIn = base64.b64decode(fileData)  # make this a open file function
        if not os.path.exists(os.getcwd() + "/Downloads/" + str(cherrypy.session.get(
                'username'))):  # reference to get current directory: https://stackoverflow.com/questions/16211703/how-to-make-a-folder-in-python-mkdir-makedirs-doesnt-do-this-right
            os.makedirs(os.getcwd() + "/Downloads/" + str(cherrypy.session.get(
                'username')))  # reference to make directory: https://stackoverflow.com/questions/273192/how-can-i-create-a-directory-if-it-does-not-exist
        with open("Downloads/" + str(cherrypy.session.get('username')) + "/" + fname,
                  'wb') as f:  # make this a open file function
            f.write(fileIn)  # make this a open file function
            f.close()
        raise cherrypy.HTTPRedirect("/displayProfile")  # after sending is done. redirect back to profile.
        return

    # @cherrypy.expose
    # @cherrypy.tools.json_in()
    # def receiveMessage(self): # BACKUP BELOW
    #    try:
    #        data = cherrypy.request.json # load json object into dictionary  
    #        dbFunctions.writeMessage(data['sender'], data['destination'], data['message'], time.strftime("%d-%m-%Y %I:%M %p", time.localtime( data['stamp']))) # Use my database helper to write received message into database. Good because database is not exposed
    #    except IndexError:
    #        return "1" #missing compulsary field
    #    return "0" #success

    @cherrypy.expose
    def imageReader(self, fname):
        f = open(fname, "rb")
        data = f.read()
        f.close()
        return data

    @cherrypy.expose
    def addToBlacklist(self, targetUser):
        dbFunctions.addToBlacklist(cherrypy.session.get('username'), targetUser)
        raise cherrypy.HTTPRedirect("/viewBlacklist")

    @cherrypy.expose
    def removeFromBlacklist(self, targetUser):
        dbFunctions.removeFromBlacklist(cherrypy.session.get('username'), targetUser)
        raise cherrypy.HTTPRedirect("/viewBlacklist")

    @cherrypy.expose
    def viewBlacklist(self):
        Blacklist = dbFunctions.getBlacklist(cherrypy.session.get('username'))
        dataReplace = {'WelcomeMessage': "Local Blacklist", 'BlackList': Blacklist}  # user list
        template = env.get_template('JaedynBlacklist.html')
        return template.render(dataReplace)

    @cherrypy.expose
    def displayProfile(self):
        try:
            profileDetails = dbFunctions.userProfile(cherrypy.session.get('username'))
            username = profileDetails[0][0]  # do the below to display empty if the user doesn't have any info ( none)
            if (username == None):
                username = ""
            Fullname = profileDetails[0][1]
            if (Fullname == None):
                Fullname = ""
            Position = profileDetails[0][2]
            if (Position == None):
                Position = ""
            Description = profileDetails[0][3]
            if (Description == None):
                Description = ""
            Location = profileDetails[0][4]
            if (Location == None):
                Location = ""
            PhotoURL = profileDetails[0][5]
            if (PhotoURL == None):
                PhotoURL = ""
            UserDetails = (
            username, Fullname, Position, Description, Location, PhotoURL, profileDetails[0][6])  # list of user details
            UserMesseges = dbFunctions.readMessages(cherrypy.session.get(
                'username'))  # read users messages in data base. Good because database is not exposed
            UserFiles = dbFunctions.readFile(cherrypy.session.get('username'))  # read all users files
            dataReplace = {'UserDetails': UserDetails, 'UserMesseges': UserMesseges,
                           'UserFiles': UserFiles}  # user list
            template = env.get_template('JaedynProfile.html')
            return template.render(dataReplace)
        except IndexError:  # user not in data base. Theoretically shouldn't happen
            raise cherrypy.HTTPRedirect("/")  # "USER NOT IN DATABASE"
        except KeyError:  # There is no username
            Page = "Sorry you are currently not logged in to the network<br/>"
            Page += "Click here to <a href='login'>login</a>."
            return Page
        except KeyError:  # There is no username
            return

    @cherrypy.expose
    def readMesseges(self):
        UserMesseges = dbFunctions.readMessages(
            cherrypy.session.get('username'))  # read users messages in data base. Good because database is not exposed
        return UserMesseges

    @cherrypy.expose  # threading to update everyone's profiles to log in server every
    def requestProfile(self, user, username):
        # self.updateUserSecurity() # Update IP, Port, Location, Public key for all current online users
        dets = dbFunctions.getReceiverDetails(str(user))
        print("IN REQUEST PROFILE")
        try:  # get receiver latest details from database
            IP = dets[0][0]  # IP
            Port = dets[0][1]  # Port
            print(IP)
            print(Port)
            if (IP == None) or (
                    Port == None):  # if no port or IP in database then we cannot send message, maybe show a error message here
                print("NO IP OR PORT")
                raise cherrypy.HTTPRedirect("/")  # user not in database
            ping = self.pingUser(username, IP, Port)  # ping receiver see if they're there FOR PEOPLE WITH NO PORT
            if (ping == "0"):  # user is online so request their profile
                print("USER ONLINE")
                print("PING PING [ING:" + ping)
                postdata = {'profile_username': user, 'sender': username}  # dictionary to be put into json
                # try:
                dest = 'http://' + IP + ":" + Port + '/getProfile?'  # BACK UP ABOVE, this LISTEN_IP/PORT should be the recievers IP/PORT instead
                # except AttributeError: # user not expecting json
                #    return "1"
                data = json.dumps(postdata)  # turns into json
                req = urllib2.Request(dest, data=data,
                                      headers={'content-type': 'application/json'})  # or json = postdata
                try:
                    response = urllib2.urlopen(req, timeout=1)  # request user profile request should get back json
                    response = response.read()
                    try:
                        dic = json.loads(response)
                    except:
                        return "1"
                except AttributeError:  # not  json
                    return "1"  # missing compulsory field
                except HTTPError:  # user doesnt have API
                    return "Doesnt have API"
                except URLError:
                    return
                except socket.timeout:
                    return
                except:
                    return
                print str(dic)
                try:
                    fullname = dic['fullname']
                except:  # user profile doesnt have details
                    fullname = "Fullname"
                if fullname == None:
                    fullname = "Fullname"
                try:
                    position = dic['position']
                except:  # user profile doesnt have details
                    position = "Position"
                if position == None:
                    position = "Position"
                try:
                    description = dic['description']
                except:  # user profile doesnt have details
                    description = "Description"
                if description == None:
                    description = "Description"
                try:
                    picture = dic['picture']
                except:  # user profile doesnt have details
                    picture = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS1pkDK_sXynQUA-qcqRbmKf-yuQhqJn9VldKnDYWkv-uu32n-vuQ"
                if picture == None:
                    picture = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS1pkDK_sXynQUA-qcqRbmKf-yuQhqJn9VldKnDYWkv-uu32n-vuQ"
                dbFunctions.updateUserProfile(str(user), str(fullname), str(position), str(description), str(
                    picture))  # if we want to thread move this function to the parent function
                # return dic implement this when threading to get multiple users
                return "0"  # success
            else:  # implement offline messaging here
                print("USER OFFLINE")
                return "3"  # not online
        except IndexError:  # Receiver is not in database
            print("USER NOT IN DATABASE")
            # raise cherrypy.HTTPRedirect("/")
            return "4"  # user not in database - database error
        return

        # raise cherrypy.HTTPRedirect("/") # after sending is done. redirect back to profile.

    @cherrypy.expose
    def searchProfile(self, user):
        user = str(user).lower().replace(" ", "")
        try:
            self.requestProfile(cherrypy.session.get('username'), user)
            profileDetails = dbFunctions.userProfile(user)
            username = profileDetails[0][0]  # do the below to display empty if the user doesn't have any info ( none)
            if (username == None):
                username = ""
            Fullname = profileDetails[0][1]
            if (Fullname == None):
                Fullname = ""
            Position = profileDetails[0][2]
            if (Position == None):
                Position = ""
            Description = profileDetails[0][3]
            if (Description == None):
                Description = ""
            Location = profileDetails[0][4]
            if (Location == None):
                Location = ""
            PhotoURL = profileDetails[0][5]
            if (PhotoURL == None):
                PhotoURL = ""
            UserDetails = (
            username, Fullname, Position, Description, Location, PhotoURL, profileDetails[0][6])  # list of user details
            UserMesseges = dbFunctions.readMessagesForSearch(cherrypy.session.get('username'),
                                                             user)  # read users messages in data base. Good because database is not exposed
            UserFiles = dbFunctions.readFileForSearch(cherrypy.session.get('username'), user)  # read all users files
            global registeredUsers
            dataReplace = {'UserDetails': UserDetails, 'UserMesseges': UserMesseges, 'UserFiles': UserFiles,
                           'UserList': registeredUsers}  # user list
            template = env.get_template('JaedynSearchProfile.html')
            return template.render(dataReplace)
        except IndexError:  # user not in data base. Theoretically shouldn't happen
            raise cherrypy.HTTPRedirect("/")  # "USER NOT IN DATABASE"
        except KeyError:  # There is no username
            Page = "Sorry you are currently not logged in to the network<br/>"
            Page += "Click here to <a href='login'>login</a>."
            return Page
        except KeyError:  # There is no username
            return

    @cherrypy.expose  # for other people to get my profile,or others on my database
    @cherrypy.tools.json_in()
    def getProfile(self):
        try:
            data = cherrypy.request.json  # load json object into dictionary
        except AttributeError:  # requested user is not returning a json
            return "1"  # missing compulsory field
        user = data['profile_username']
        try:
            profileDetails = dbFunctions.userProfile(user)  # get esuer
            username = profileDetails[0][0]
            Fullname = profileDetails[0][1]
            Position = profileDetails[0][2]
            Description = profileDetails[0][3]
            Location = profileDetails[0][4]
            PhotoURL = profileDetails[0][5]
            dic = {'fullname': profileDetails[0][1], 'position': profileDetails[0][2],
                   'description': profileDetails[0][3], 'location': profileDetails[0][4],
                   'picture': profileDetails[0][5]}
            jsonData = json.dumps(dic)
            return jsonData
        except IndexError, KeyError:  # Searched user is not in the database. MAKE A NO USER FOUND HTML?
            dic = {'fullname': None, 'position': None, 'description': None, 'location': None, 'picture': None}
            jsonData = json.dumps(dic)
            return jsonData

    @cherrypy.expose
    def editProfile(self):
        try:
            profileDetails = dbFunctions.userProfile(cherrypy.session.get('username'))
            username = profileDetails[0][0]
            name = profileDetails[0][1]
            Position = profileDetails[0][2]
            Description = profileDetails[0][3]
            Location = profileDetails[0][4]
            PhotoURL = profileDetails[0][5]
            # ReaderFunctions.downloadWebImage(PhotoURL, cherrypy.session.get('username')) # downloads image locally
            ProfilePic = ReaderFunctions.readProfilePicHTML("ProfilePage.html",
                                                            cherrypy.session.get('username'))  # test idk
            Page = username + " this is your proile! <br/>"
            Page += ProfilePic
            Page += "Full Name: " + name + " <br/>"
            Page += "Position " + Position + " <br/>"
            Page += "Full Description: " + Description + " <br/>"
            Page += "Location: " + str(
                Location) + " (0: University LAN, 1: University WIFI, 2: Rest of the world) <br/>"
            Page += '<form accept-charset="utf-8" action="/saveProfileEdit" method="post" enctype="multipart/form-data">'
            Page += 'Full Name: <input type="text" size="100" name = "FullName" placeholder="Fullname" required="" autofocus="" "/><br/>'
            Page += 'Position: <input type="text" size="100" name = "Position" placeholder="Position" required="" autofocus="""/><br/>'
            Page += 'Description: <input type="text" size="100" name = "Description" placeholder="Description" required="" autofocus="""/><br/>'
            Page += 'PictureURL: <input type="text" size="100" name = "PhotoURL" placeholder="URL to JPG/PNG Image" required="" autofocus="" "/><br/>'
            Page += '<input type="submit" value="Save Changes"/></form>'
            Page += "<a href='displayProfile'>Cancel</a>."
            Page += "<br/><a href='/'>Home</a>."
            # Page += ProfilePic
        except KeyError:  # There is no username
            Page = "Sorry you are currently not logged in to the network<br/>"
            Page += "Click here to <a href='login'>login</a>."
        return Page

    @cherrypy.expose
    def saveProfileEdit(self, FullName, Position, Description, PhotoURL):
        dbFunctions.updateUserProfile(cherrypy.session.get('username'), FullName, Position, Description, PhotoURL)
        raise cherrypy.HTTPRedirect("/displayProfile")

    @cherrypy.expose
    def login(self):  # log in screen
        Page = ReaderFunctions.readSignInHTML("HTML/JaedynSignIn.html")
        return Page

    # @cherrypy.expose # back up above
    # def login(self): # log in screen
    #    data = ReaderFunctions.readHTM("HTML/index.html")
    #    return data

    # @cherrypy.expose
    # def loginError(self):
    #    Page = ReaderFunctions.readSignInHTML("HTML/JaedynSignIn.html")
    #    return Page

    @cherrypy.expose
    def css(self, fname):
        f = open(fname, "r")
        data = f.read()
        f.close()
        return data

    # @cherrypy.expose
    # def img(self, fname):
    #    f = open(fname, "rb")
    #    data = f.read()
    #    f.close()
    #    return data

    @cherrypy.expose
    def GetServerListOfUsers(self):
        try:
            username = cherrypy.session.get('username')
            password = cherrypy.session.get('password')
            request = Request('http://cs302.pythonanywhere.com/listUsers?')
            response = urlopen(request)
            code = response.read()
            Page = "User List: " + code + " <br/>"
        except KeyError:
            Page = "Sorry you are not logged in: <br/>"
        return Page

    @cherrypy.expose
    def GetOnlineUsers(self):  # BACKUP BELOW
        try:
            username = cherrypy.session.get('username')
            password = cherrypy.session.get('password')
            request = Request(
                'http://cs302.pythonanywhere.com/getList?username=' + username + '&password=' + password + '&enc=0&json=1')
            response = urlopen(request)
            dic = response.read()  # should give back json
            dic = json.loads(dic)  # should give back dict
            # try:
            #   dic = json.loads(dic) # should give back dict
            # except ValueError: # if getting two json, split and read the first one - hack fix
            #    dic = json.loads(dic.split(';')[0])
            Page = "Number of users online: " + str(len(dic)) + " <br/><br/>"
            for userNum in dic:
                json_data = dic[str(userNum)]['username'] + "   " + dic[str(userNum)]['location'] + "   " + \
                            dic[str(userNum)]['ip'] + "  "
                json_data += dic[str(userNum)]['port'] + "   " + dic[str(userNum)]['lastLogin']
                try:
                    json_data += dic[str(userNum)]['publicKey']  # add public key if available
                except KeyError:  # no decrytion key
                    json_data = json_data
                Page += "User" + str(userNum) + " details: " + str(json_data) + " <br/>"
        except KeyError:
            Page = "Sorry you are not logged in: <br/>"
        return Page

    # @cherrypy.expose
    # def updateUserSecurity(self): # BACKUP BELOW
    # try:
    #    username = cherrypy.session.get('username')
    #    password = cherrypy.session.get('password')
    #    request = Request('http://cs302.pythonanywhere.com/getList?username='+username+'&password='+password+'&enc=0&json=1')
    #    response = urlopen(request)
    #    dic = response.read() # should give back json
    #    dic = json.loads(dic) # should give back dict
    #    for userNum in dic:
    #        User = dic[str(userNum)]['username']
    #        Location = dic[str(userNum)]['location']
    #        IP = dic[str(userNum)]['ip']
    #        Port = dic[str(userNum)]['port']
    #        LastLogin =  dic[str(userNum)]['lastLogin']
    #        try:
    #            PublicKey = dic[str(userNum)]['publicKey'] # add public key if available
    #            dbFunctions.updateUserPublicKey(User, PublicKey)
    #        except KeyError: # no decrytion key
    #            pass
    #        dbFunctions.updateUsersDetails(User, IP, Port, LastLogin)
    #        dbFunctions.updateUserLocation(User, Location)
    # except KeyError:
    #    raise cherrypy.HTTPRedirect("/")
    # return

    @cherrypy.expose
    def listAPI(self):  # /API[arguments][argument(opt)].....
        return "0"

    @cherrypy.expose
    def pingUser(self, Requester, IP, Port):  # BACKUP BELOW
        if (IP == None) or (Port == None):
            return
        print("Pinging: " + str(Requester))
        request = Request('http://' + IP + ":" + Port + '/ping?sender=' + Requester)  # BACK UP ABOVE
        try:
            response = urlopen(request, timeout=0.8)
            code = response.read()
            return code[0]
        except:
            pass
        return "IDK"

    @cherrypy.expose
    def updateOthersStatus(self):
        global threadCount
        if threadCount < 4:  # if its the first time the server is loading up
            global threadCount
            threadCount += 1
            print(str(threadCount))
            threading.Timer(40, self.updateOthersStatus).start()  # get everyones profile every 30 seconds.
            return
        request = Request('http://cs302.pythonanywhere.com/listUsers?')  # get list of all registered userss
        req = urllib2.urlopen(request)
        data = req.read()
        dataList = data.split(",")  # split into list
        for x in dataList:
            dets = dbFunctions.getReceiverDetails(x)
            try:  # get receiver latest details from database
                IP = dets[0][0]  # IP
                Port = dets[0][1]  # Port
            except IndexError:  # Receiver is not in database
                return
            try:
                ping = self.pingUser("jdam534", IP, Port)  # request profile of all
            except:
                pass
            if ping == "0":
                status = "Online"
                try:
                    url = 'http://' + IP + ':' + Port + '/getStatus'
                    payload = {'profile_username': str(x)}
                    jsonData = json.dumps(payload)
                    request = urllib2.Request(url, data=jsonData,
                                              headers={'content-type': 'application/json'})  # or json = postdata
                    req = urllib2.urlopen(request, timeout=0.6)
                    dic = json.loads(req.read())
                    print x
                    print dic
                    print dic['status']
                    status = str(dic['status'])
                except socket.timeout:
                    pass
                except:
                    pass
            else:
                status = "Offline"
            dbFunctions.updateUserStatus(status, x)  # update users stats
        threading.Timer(40, self.updateOthersStatus).start()  # get everyones profile every 30 seconds.
        return

    @cherrypy.expose
    @cherrypy.tools.json_in()
    def receiveMessage(self):  # BACKUP BELOW
        data = cherrypy.request.json  # load json object into dictionary
        Blacklist = dbFunctions.getBlacklist(cherrypy.session.get('username'))
        for x in Blacklist:
            if data['sender'] == x[2]:  # check if sender is in the local user's blacklist
                return "11"  # code for black listed
        dbFunctions.writeMessage(data['sender'], data['destination'], data['message'],
                                 time.strftime("%d-%m-%Y %I:%M %p", time.localtime(data[
                                                                                       'stamp'])))  # Use my database helper to write received message into database. Good because database is not exposed
        return "0"

    @cherrypy.expose
    def sendMessage(self, message, destination):
        # self.updateUserSecurity() # Update IP, Port, Location, Public key for all current online users
        dets = dbFunctions.getReceiverDetails(destination)
        try:  # get receiver latest details from database
            IP = dets[0][0]  # IP
            Port = dets[0][1]  # Port
            PublicKey = dets[0][2]  # Public key
            if (IP == None) or (
                    Port == None):  # if no port or IP in database then we cannot send message, maybe show a error message here
                raise cherrypy.HTTPRedirect("/displayProfile")
            ping = self.pingUser(cherrypy.session.get('username'), IP, Port)  # ping receiver see if they're there
            if (ping == "0"):  # user is online so end them a message
                # if (PublicKey != none): # if they have a public key then encrypt with their public key
                # encyrpt message with public key
                now = float(time.mktime(time.localtime()))
                postdata = {'sender': cherrypy.session.get('username'), 'destination': str(destination),
                            'message': message, 'stamp': now, 'markdown': 0, 'encoding': 0, 'encryption': 0,
                            'hashing': 0, 'hashed': '0', 'decryptionKey': '0'}  # dictionary to be put into json
                dest = 'http://' + IP + ":" + Port + '/receiveMessage'  # BACK UP ABOVE, this LISTEN_IP/PORT should be the recievers IP/PORT instead
                data = json.dumps(postdata)  # turns into json
                req = urllib2.Request(dest, data=data,
                                      headers={'content-type': 'application/json'})  # or json = postdata
                try:
                    response = urllib2.urlopen(req)  # send user message json dic encoded
                    if (response.read() == "0"):
                        dbFunctions.writeMessage(cherrypy.session.get('username'), str(destination), str(message),
                                                 time.strftime("%d-%m-%Y %I:%M %p", time.localtime(now)))
                except URLError, HTTPError:
                    pass
                print "Message sent to server."
            else:  # implement offline messaging here
                if destination == cherrypy.session.get('username'):
                    raise cherrypy.HTTPRedirect("/displayProfile")  # placeholder for offline messaging
                else:
                    raise cherrypy.HTTPRedirect(
                        "/searchProfile?user=" + destination)  # placeholder for offline messaging
            # return "USER IS OFFLINE" # for test
        except IndexError:  # Receiver is not in database
            if destination == cherrypy.session.get('username'):
                raise cherrypy.HTTPRedirect("/displayProfile")  # placeholder for offline messaging
            else:
                raise cherrypy.HTTPRedirect(
                    "/searchProfile?user=" + destination)  # placeholder for offline messaging
        if destination == cherrypy.session.get('username'):
            raise cherrypy.HTTPRedirect("/displayProfile")  # placeholder for offline messaging
        else:
            raise cherrypy.HTTPRedirect("/searchProfile?user=" + destination)  # placeholder for offline messaging

    # LOGGING IN AND OUT
    @cherrypy.expose
    def signin(self, username=None, password=None):
        """Check their name and password and send them either to the main page, or back to the main login screen."""
        username = str(username)
        password = str(password)  # change non type into string
        password = hashlib.sha256(password + "COMPSYS302-2017").hexdigest()  # encrypt password
        error = self.authoriseUserLogin(username, password)
        if (error == "0"):  # success
            cherrypy.session['username'] = username  # store session username
            cherrypy.session['password'] = password  # store session password encrypted
            dic = {'username': username, 'password': password,
                   'signedIn': True}  # store credentials in a dictionary for threading
            print("before thread init")
            global threadCount
            threadCount = 1
            self.multiThreadingInit(dic)  # initialize and start threading process
            print("before thread init")
            raise cherrypy.HTTPRedirect('/')
        else:  # not successful
            raise cherrypy.HTTPRedirect('login')

    # threading update user DB, reporting to log in server. CAN ONLY DO 7 CALLS TOTAL PER MINUTE. MAYBE LATER ADD THESE MULTITHREADING FUNCTION TO THEIR OWN FILE WITHOUT IT CRASHING
    # @cherrypy.expose
    def multiThreadingInit(self,
                           dic):  # initialize threading with dictionary of details needed (username and password) #username = dic['username']
        print("after multi thread call")
        self.updateUserSecurity(dic['username'], dic['password'], dic['signedIn'])
        self.updateOthersStatus()
        self.threadUserProfiles(dic['username'], dic['password'], dic['signedIn'])
        self.reportToServer(dic['username'], dic['password'], dic[
            'signedIn'])  # maybe start this thread when server starts anad goes through every user thats online?
        # threading.Timer(15, self.threadUserProfiles, args=(dic['username'], dic['password'], dic['signedIn'])).start() # get everyones profile every 30 seconds.
        # threading.Timer(30, self.updateUserSecurity, [dic['username'], dic['password'], dic['signedIn']]).start() # report to log in server every 30 seconds.
        # threading.Timer(40, self.reportToServer, [dic['username'], dic['password'], dic['signedIn']]).start() # report to log in server every 30 seconds.
        # this way is only calling it once
        # thread to get user profiles
        # thread to get user status'
        return

    def threadUserProfiles(self, username, password, signedIn):  # Updating user profiles. Once
        print("Outside of signed in")
        if (signedIn):  # if user is signed in do threading
            global threadCount
            if threadCount < 4:  # if its the first time the server is loading up
                global threadCount
                print(str(threadCount))
                threadCount += 1
                threading.Timer(60, self.threadUserProfiles,
                                args=(username, password, signedIn)).start()  # get everyones profile every 30 seconds.
                return
            print("Inside of signed in")
            request = Request('http://cs302.pythonanywhere.com/listUsers?')  # get list of all registered userss
            req = urllib2.urlopen(request)
            data = req.read()
            dataList = data.split(",")  # split into list
            for x in dataList:
                print x
                profileData = self.requestProfile(x, username)  # request profile of all
            threading.Timer(60, self.threadUserProfiles,
                            args=(username, password, signedIn)).start()  # get everyones profile every 30 seconds.
        return  # theory should never get here unless signed out

    # @cherrypy.expose
    def updateUserSecurity(self, username, password,
                           signedIn):  # Threading to update people who are online IP/Port Location etc.
        print("before user security thread")
        if (signedIn):  # if user is signed in do threading
            global threadCount
            if threadCount < 4:  # if its the first time the server is loading up
                global threadCount
                threadCount += 1
                print(str(threadCount))
                threading.Timer(50, self.updateUserSecurity, args=(username, password,
                                                                   signedIn)).start()  # report to log in server every 30 seconds. calls the function agais
                return
            print("before thread init")
            # username = cherrypy.session.get('username')
            # password = cherrypy.session.get('password')
            request = Request(
                'http://cs302.pythonanywhere.com/getList?username=' + username + '&password=' + password + '&enc=0&json=1')
            print("before user security thread")
            response = urlopen(request)
            dic = response.read()  # should give back json
            dic = json.loads(dic)  # should give back dict
            for userNum in dic:
                print(str(userNum))
                User = dic[str(userNum)]['username']
                Location = dic[str(userNum)]['location']
                IP = dic[str(userNum)]['ip']
                Port = dic[str(userNum)]['port']
                LastLogin = dic[str(userNum)]['lastLogin']
                try:
                    PublicKey = dic[str(userNum)]['publicKey']  # add public key if available
                    dbFunctions.updateUserPublicKey(User, PublicKey)
                except KeyError:  # no decrytion key
                    pass  # do nothing
                dbFunctions.updateUsersDetails(User, IP, Port, LastLogin)
                dbFunctions.updateUserLocation(User, Location)
            threading.Timer(50, self.updateUserSecurity, args=(
            username, password, signedIn)).start()  # report to log in server every 30 seconds. calls the function agais
            print("after user security thread")
        return

        # @cherrypy.expose        # threading to report to log in server every

    def reportToServer(self, username, password, signedIn):
        if (signedIn):  # if user is signed in do threading
            global threadCount
            if threadCount < 4:  # if its the first time the server is loading up
                global threadCount
                threadCount += 1
                print(str(threadCount))
                threading.Timer(40, self.reportToServer, args=(
                username, password, signedIn)).start()  # report to log in server every 20 seconds.
                return
            request = Request(
                'http://cs302.pythonanywhere.com/report?username=' + username + '&password=' + password + '&location=' + location + '&ip=' + listen_ip + '&port=' + str(
                    listen_port) + '&enc=0')
            print("before user reqport thread")
            threading.Timer(40, self.reportToServer,
                            args=(username, password, signedIn)).start()  # report to log in server every 20 seconds.
            print("after user reprot thread")
            return

    @cherrypy.expose
    def signout(self):
        """Logs the current user out, expires their session"""
        try:
            error = self.authoriseUserLogoff(cherrypy.session.get('username'), cherrypy.session.get('password'))
        except KeyError:  # no username
            raise cherrypy.HTTPRedirect('/loginError')
        if (error == "0"):
            global threadCount
            threadCount = 0
            cherrypy.session.clear()
            raise cherrypy.HTTPRedirect('/')
        else:
            cherrypy.lib.sessions.expire()
            raise cherrypy.HTTPRedirect('/')

    def authoriseUserLogin(self, username, password):  # hidden for security
        print username
        print password
        # request = Request('http://cs302.pythonanywhere.com/report?username='+username+'&password='+password+'&location=0&ip=10.104.131.39&port=10003&enc=0')
        request = Request(
            'http://cs302.pythonanywhere.com/report?username=' + username + '&password=' + password + '&location=' + location + '&ip=' + listen_ip + '&port=' + str(
                listen_port) + '&enc=0')
        try:
            response = urlopen(request)
            code = response.read()
            return code[0]
        except URLError, e:
            return 'Error Code:', e

    def authoriseUserLogoff(self, username, password):  # hidden for securuity
        print username
        print password
        request = Request(
            'http://cs302.pythonanywhere.com/logoff?username=' + username + '&password=' + password + '&enc=0')
        try:
            response = urlopen(request)
            code = response.read()
            return code[0]
        except URLError, e:
            return 'Error Code:', e


def runMainApp():
    # Create an instance of MainApp and tell Cherrypy to send all requests under / to it. (ie all of them)
    cherrypy.tree.mount(MainApp(), "/")

    # Tell Cherrypy to listen for connections on the configured address and port.
    cherrypy.config.update({'server.socket_host': listen_ip,
                            'server.socket_port': listen_port,
                            'engine.autoreload.on': True,
                            'tools.gzip.on': True,
                            'tools.gzip.mime_types': ['text/*'],
                            })

    server = Server()
    server.socket_port = 10000
    server.subscribe()

    print "========================="
    print "Jaedyn Damms - 955581057"
    print "COMPSYS302 - Software Design Application"
    print "Type: http://" + listen_ip + ":" + str(listen_port) + "    to launch the application"
    print "IP Address: " + listen_ip
    print "Listening Port: " + str(listen_port)
    print "========================================"
    webbrowser.open("http://" + listen_ip + ":" + str(listen_port), new=0,
                    autoraise=True)  # opens up client in new web browser, automatically raises it up

    # Start the web server
    cherrypy.engine.start()

    # And stop doing anything else. Let the web server take over.
    cherrypy.engine.block()


# Run the function to start everything
runMainApp()
