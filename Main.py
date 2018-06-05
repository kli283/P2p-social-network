#!/usr/bin/python
""" Main.py

    COMPSYS302 - Software Design
    Author: Andrew Chen (andrew.chen@auckland.ac.nz)
    Modified by: Kenny Li (kli283@aucklanduni.ac.nz)
    Last Edited: 03/06/2018

    This program uses the CherryPy web server (from www.cherrypy.org).
"""
# Requires:  CherryPy 3.2.2  (www.cherrypy.org)
#            Python  (We use 2.7)

# The address we listen for connections on
import base64
import mimetypes
import socket
# import sys
#
# reload(sys)
# sys.setdefaultencoding('utf8')
import os

from BasicFunctions import encrypt_string, split_upi

listen_ip = "0.0.0.0"
listen_port = 10001

import cherrypy
import urllib
import urllib2
import sqlite3
import json
import time
import DatabaseFunctions
import threading
from jinja2 import Environment, FileSystemLoader, select_autoescape


class MainApp(object):
    # CherryPy Configuration
    _cp_config = {'tools.encode.on': True,
                  'tools.encode.encoding': 'utf-8',
                  'tools.sessions.on': 'True',
                  }

    enableThread = {}
    rateCounter = {}


    DatabaseFunctions.init_current_user()

    # Gets current directory
    CUR_DIR = os.path.dirname(os.path.abspath(__file__))
    env = Environment(
        loader=FileSystemLoader(CUR_DIR),
        trim_blocks=True,
        autoescape=select_autoescape(['html'])
    )

    # The function to logout is called here once the server is stopped.
    def __init__(self):
        cherrypy.engine.subscribe('stop', self.shutdown)
        thread = threading.Thread(target=self.threadRate)
        thread.daemon = True
        thread.start()

    #Rate Limiting function
    def rateCount(self):

        return "-----User is blocked, too many requests-----"

    # If they try somewhere we don't know, catch it here and send them to the right place.
    @cherrypy.expose
    def default(self, *args, **kwargs):
        """The default page, given when we don't recognise where the request is for."""
        Page = "I don't know where you're trying to go, so have a 404 Error."
        cherrypy.response.status = 404
        return Page

    @cherrypy.expose
    def index(self):
        DatabaseFunctions.init_current_user()
        template = self.env.get_template('index.html')
        loginTemplate = self.env.get_template('login.html')

        try:
            # Page += "Hello " + cherrypy.session['username'] + "!<br/>"
            # Page += "Here is some bonus text because you've logged in!" + "!<br/>"
            # Page += "Click here to <a href='logout'>logout</a>" + "!<br/>"
            # Page += "Click here to view list of users <a href='showUsers'>BAM</a>." + "!<br/>"
            # Page += "See who's <a href='showOnline'>ONLINE</a>." + "!<br/>"
            # Page += cherrypy.session['username'] + " is Username" + "!<br/>"
            # Page += cherrypy.session['password'] + " is Password" + "!<br/>"
            # Page += "Click here to go to <a href='showMessages'>messages</a>." + "!<br/>"
            # Page += "Click here to go to <a href='showProfiles'>profiles</a>." + "!<br/>"
            # Page += "Click here to edit your <a href='editProfile'>profile</a>." + "!<br/><br/>"
            # Page += "Click here to send a <a href='showFile'>file</a>." + "!<br/><br/>"
            userList = self.listUsers()
            userDictionary = self.showOnline()
            onlineUsers = []
            # user = DatabaseFunctions.get_current_user()
            # user = user[0][1]

            user = cherrypy.session['username']
            try:
                profileDetails = DatabaseFunctions.get_user_profile(user)
                try:
                    updateTime = time.strftime("%d-%m-%Y %I:%M %p", time.localtime(float(profileDetails[0][7])))
                except:
                    updateTime = "Time for last updated is not available"

            except:
                profileDetails = "No profile available"
            for userNum in userDictionary:
                onlineUsers.append(userDictionary[str(userNum)]['username'])
            return template.render(user=user, userList=userList, profile=profileDetails, time=updateTime)

        except KeyError:  # No username
            print("-----User is not logged on-----")
            return loginTemplate.render()

    @cherrypy.expose
    def login(self):
        return file("login.html")  # urllib.urlopen("index.html").read()

    @cherrypy.expose
    def logout(self):
        # Page = '<form action="/signin" method="post" enctype="multipart/form-data">'
        error = self.logoff(cherrypy.session['username'], cherrypy.session['password'])
        if (error == 0):
            cherrypy.session.clear()
            raise cherrypy.HTTPRedirect('/')
        else:
            raise cherrypy.HTTPRedirect('/')

    @cherrypy.expose
    def showMessages(self, username=None):
        try:
            if username is None:
                username = cherrypy.session['username']
            # user = DatabaseFunctions.get_current_user()
            # user = user[0][1]
            user = cherrypy.session['username']
            userDictionary = self.showOnline()
        except KeyError:  # No username
            print("-----User is not logged on-----")
            raise cherrypy.HTTPRedirect("/")

        template = self.env.get_template('Message.html')
        myPic = DatabaseFunctions.get_user_profile(user)
        friendPic = DatabaseFunctions.get_user_profile(username)
        convo = DatabaseFunctions.get_convo(user, username)
        try:
            friendPic = friendPic[0][6]
        except:
            print("-----No profile pic-----")
        try:
            myPic = myPic[0][6]
        except:
            print("-----No profile pic-----")

        recipient = username
        try:
            return template.render(title='Messages', messages=convo, profilePic=friendPic, otherPic=myPic,
                                   onlineUsers=userDictionary, user=user, sender=recipient)
        except:
            print("-----Problems with reading message. Other user may have encryption-----")

    @cherrypy.expose
    def showFile(self):
        try:
            Page = '<form action="/sendFile" method="post" enctype="multipart/form-data">'
            Page += 'Select file: <input type="file" name="fileData" ><br/>'
            Page += 'Receiver: <input type="text" name="recipient"/><br/>'
            Page += '<input type="submit" value="Send"/></form>'

            userDictionary = self.showOnline()

            Page += "Here is a list of people online from COMPSYS302!<br/>"
            Page += "Number of users online: " + str(len(userDictionary)) + " <br/><br/>"
            for userNum in userDictionary:
                Page += userDictionary[str(userNum)]['username'] + " <br/>"
            return Page
        except KeyError:  # No username
            print("-----User is not logged on-----")
            raise cherrypy.HTTPRedirect("/")

    @cherrypy.expose
    @cherrypy.tools.json_in()
    def showOnline(self):
        userData = urllib.urlencode(
            {'username': cherrypy.session['username'], 'password': cherrypy.session['password']})
        r = urllib.urlopen('http://cs302.pythonanywhere.com/getList?&enc=0&json=1', userData)

        userDictionary = r.read()
        userDictionary = json.loads(userDictionary)

        DatabaseFunctions.add_online_db(userDictionary)
        return userDictionary


    @cherrypy.expose
    def sum(self, a=0, b=0):  # All inputs are strings by default
        output = int(a) + int(b)
        return str(output)

    # LOGGING IN AND OUT
    @cherrypy.expose
    def signin(self, username, password, location):
        # TODO CHECK IF PUBLIC IP DIFFERS FROM LOCAL
        local_ip = self.getIp()

        port = '10001'
        # DatabaseFunctions.init_current_user()
        DatabaseFunctions.add_current_user(username, encrypt_string(username, password), location)

        Details = DatabaseFunctions.get_current_user()
        """Check their name and password and send them either to the main page, or back to the main login screen."""
        error = self.reportLogin(username, password, location, local_ip, port)
        if error == 0:
            cherrypy.session['username'] = username
            cherrypy.session['password'] = encrypt_string(username, password)
            thread = threading.Thread(target=self.threadLogin, args=(username, password, location))
            self.enableThread[username] = True
            # self.enableThread = True
            thread.daemon = True
            thread.start()
            raise cherrypy.HTTPRedirect('/')
        else:
            raise cherrypy.HTTPRedirect('/login')

    @cherrypy.expose
    def threadLogin(self, username, password, location):
        ip = self.getIp()
        port = DatabaseFunctions.get_port(username)
        while self.enableThread[username]:
            self.reportLogin(username, password, location, ip, port)
            print "-----Reporting Login-----"
            time.sleep(30)

    @cherrypy.expose
    def threadRate(self):
        while True:
            print "-----Rate limiting timer-----"
            self.rateCounter.clear()
            time.sleep(60)

    def reportLogin(self, username, password, location, ip, port):
        userData = urllib.urlencode(
            {'username': username, 'password': encrypt_string(username, password), 'location': location,
             'ip': ip, 'port': port})
        r = urllib.urlopen('http://cs302.pythonanywhere.com/report', userData)

        returnCode = int(r.read()[0:1])
        return returnCode

    def getIp(self):
        """Acquires the current ip address"""
        s = socket.socket(socket.AF_INET,
                          socket.SOCK_DGRAM)  # Code from https://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        public_ip = urllib.urlopen('http://ip.42.pl/raw').read() #Was used when testing with port forwarding
        return ip

    @cherrypy.expose
    def logoff(self, username, password):
        userData = urllib.urlencode({'username': username, 'password': password})
        r = urllib.urlopen('http://cs302.pythonanywhere.com/logoff', userData)
        self.enableThread[username] = False
        DatabaseFunctions.drop_current_user(username)
        returnCode = int(r.read()[0:1])
        return returnCode

    def listUsers(self):
        r = urllib.urlopen('http://cs302.pythonanywhere.com/listUsers')

        userList = split_upi(r.read())
        # DatabaseFunctions.add_upi_db(userList)
        return userList

    @cherrypy.expose
    def pingUser(self, username, IP, port):
        # print('http://' + IP + ":" + port + '/ping?sender=' + username)
        request = urllib2.Request('http://' + IP + ":" + port + '/ping?sender=' + username)
        response = urllib2.urlopen(request, timeout=0.8)
        errorCode = response.read()
        return errorCode[0]

    @cherrypy.expose
    def ping(self, sender):

        ip = cherrypy.request.remote.ip
        if ip in self.rateCounter:
            self.rateCounter[ip] += 1
            if self.rateCounter[ip] > 100:
                print("-----Request rejected, currently being rate limited-----")
                return "11"
            else:
                return "0"
        else:
            self.rateCounter[ip] = 1
            return "0"

        # try:
        #     self.rateCounter[ip] += 1
        #     if self.rateCounter[sender] > 100:
        #         print("-----Request rejected, currently being rate limited-----")
        #         return "11"
        #     else:
        #         return "0"
        # except:
        #     self.rateCounter[ip] = 0
        #     # self.rateCounter[ip] += 1
        #     print(self.rateCounter)
        #     return "0"


    @cherrypy.expose
    @cherrypy.tools.json_in()
    def receiveMessage(self):
        ip = cherrypy.request.remote.ip
        if ip in self.rateCounter:
            self.rateCounter[ip] += 1
            if self.rateCounter[ip] > 100:
                print("-----Request rejected, currently being rate limited-----")
                return "11"
            else:
                input_data = cherrypy.request.json
                sender = input_data['sender']
                receiver = input_data['destination']
                message = input_data['message']
                timestamp = input_data['stamp']
                DatabaseFunctions.add_msg_db(sender, receiver, message, timestamp)
                return "0"
        else:
            self.rateCounter[ip] = 1
            input_data = cherrypy.request.json
            sender = input_data['sender']
            receiver = input_data['destination']
            message = input_data['message']
            timestamp = input_data['stamp']
            DatabaseFunctions.add_msg_db(sender, receiver, message, timestamp)
            return "0"




    @cherrypy.expose
    def sendMessage(self, recipient, message):
        """This is the function that sends the message.
        It would first try to see whether the recipient
        is online, then send the message.
        """
        try:
            currentTime = float(time.time())
            destinationIp = DatabaseFunctions.get_ip(recipient)
            destinationPort = DatabaseFunctions.get_port(recipient)
            try:
                pingCode = self.pingUser(cherrypy.session['username'], destinationIp, destinationPort)
                messageDict = {"sender": cherrypy.session['username'], "message": message, "destination": recipient,
                               "stamp": currentTime}
                messageDict = json.dumps(messageDict)
            except:
                print("------Message failed to send, unable to ping recipient------")
                raise cherrypy.HTTPRedirect('/showMessages?username={}'.format(recipient))
            if (pingCode == '0'):
                url = 'http://' + destinationIp + ":" + destinationPort + '/receiveMessage'
                req = urllib2.Request(url, data=messageDict, headers={'content-type': 'application/json'})
                response = urllib2.urlopen(req)
                if (response.read() == '0'):
                    DatabaseFunctions.add_msg_db(cherrypy.session['username'], recipient, message, currentTime)
                    print("-----Message successfully sent-----")
                    raise cherrypy.HTTPRedirect('/showMessages?username={}'.format(recipient))
        except KeyError:  # No username
            print("-----User is not logged on-----")
            raise cherrypy.HTTPRedirect("/")

    @cherrypy.expose
    @cherrypy.tools.json_in()
    def getProfile(self):
        ip = cherrypy.request.remote.ip
        input_data = cherrypy.request.json
        UPI = input_data["profile_username"]
        profile = DatabaseFunctions.get_user_profile(UPI)
        output_dict = {"lastUpdated": profile[0][7], "fullname": profile[0][2],
                       "position": profile[0][3], "description": profile[0][4],
                       "location": profile[0][5], "picture": profile[0][6]}
        output_dict = json.dumps(output_dict)
        if ip in self.rateCounter:
            self.rateCounter[ip] += 1
            if self.rateCounter[ip] > 100:
                print("-----Request rejected, currently being rate limited-----")
                return "11"
            else:
                return output_dict
        else:
            self.rateCounter[ip] = 1
            return output_dict



    @cherrypy.expose
    def acquireProfile(self, userProfile):
        postdata = {'profile_username': userProfile, 'sender': cherrypy.session['username']}
        destinationIp = DatabaseFunctions.get_ip(userProfile)
        destinationPort = DatabaseFunctions.get_port(userProfile)
        try:
            # pingCode = self.pingUser(cherrypy.session['username'], destinationIp, destinationPort)
            # if (pingCode == '0'):
            url = 'http://' + destinationIp + ":" + destinationPort + '/getProfile?'
            data = json.dumps(postdata)
            req = urllib2.Request(url, data=data, headers={'content-type': 'application/json'})
            response = urllib2.urlopen(req, timeout=1)
            response = response.read()
            profileDict = json.loads(response)

            name = profileDict.get('fullname', 'Not Available')
            position = profileDict.get('position', 'Not Available')
            description = profileDict.get('description', 'Not Available')
            location = profileDict.get('location', 'Not Available')
            picture = profileDict.get('picture', 'Not Available')
            timestamp = profileDict.get('lastUpdated', 'Not Available')
            DatabaseFunctions.add_profile(userProfile, name, position, description, location, picture, timestamp)
        except:
            print("-----Something went wrong trying to acquire profile-----")
            pass

    @cherrypy.expose
    def requestProfile(self, userProfile):
        try:
            template = self.env.get_template('Profile.html')
            error = ""
            try:
                destinationIp = DatabaseFunctions.get_ip(userProfile)
                destinationPort = DatabaseFunctions.get_port(userProfile)
                try:
                    pingCode = self.pingUser(cherrypy.session['username'], destinationIp, destinationPort)
                    if (pingCode == '0'):
                        self.acquireProfile(userProfile)
                except:
                    print("-----Something went wrong trying to acquire profile-----")
            except:
                error += "user does not exist"
                print("-----user does not exist-----")
            userList = self.listUsers()

            try:
                profile = DatabaseFunctions.get_user_profile(userProfile)
            except:
                error += "No profile available"
                userProfile = DatabaseFunctions.get_current_user()
                userProfile = userProfile[0][1]
                profile = DatabaseFunctions.get_user_profile(userProfile)
            try:
                updateTime = time.strftime("%d-%m-%Y %I:%M %p", time.localtime(float(profile[0][7])))
            except:
                updateTime = "Time for last updated is not available"
            try:
                return template.render(user=userProfile, userList=userList, profile=profile, time=updateTime, error=error)
            except:
                raise cherrypy.HTTPRedirect('/')
        except KeyError:  # No username
            print("-----User is not logged on-----")
            raise cherrypy.HTTPRedirect("/")

    @cherrypy.expose
    def editProfile(self):
        try:
            currentUser = DatabaseFunctions.get_current_user()
            # currentUser = currentUser[0][1]
            currentUser = cherrypy.session['username']
            profile = DatabaseFunctions.get_user_profile(currentUser)
            UPI = profile[0][1]
            name = profile[0][2]
            position = profile[0][3]
            description = profile[0][4]
            location = profile[0][5]
            picture = profile[0][6]
            # timestamp = time.time()

            Page = UPI + " this is your profile! <br/>"
            Page += '<img src=' + picture + ' alt="Kennys profile" style = "max-width: 500px; max-height: 500px">'
            Page += "<br/> " + "Full Name: " + name + " <br/>"
            Page += "Position " + position + " <br/>"
            Page += "Full Description: " + description + " <br/>"
            Page += "Location: " + location + " <br/>"
            Page += '<form accept-charset="utf-8" action="/saveProfile" method="post" enctype="multipart/form-data">'
            Page += 'Full Name: <input type="text" size="100" name = "name" placeholder="Fullname" required="" autofocus="" "/><br/>'
            Page += 'Position: <input type="text" size="100" name = "position" placeholder="Position" required="" autofocus="""/><br/>'
            Page += 'Description: <input type="text" size="100" name = "description" placeholder="Description" required="" autofocus="""/><br/>'
            Page += 'Location: <input type="text" size="100" name = "location" placeholder="Location" required="" autofocus="" "/><br/>'
            Page += 'Picture: <input type="text" size="100" name = "picture" placeholder="URL of Image" required="" autofocus="" "/><br/>'
            Page += '<input type="submit" value="Save Changes"/></form>'
            return Page
        except KeyError:  # No username
            print("-----User is not logged on-----")
            raise cherrypy.HTTPRedirect("/")


    @cherrypy.expose
    def saveProfile(self, name, position, description, location, picture):
        timestamp = float(time.time())
        DatabaseFunctions.add_profile(cherrypy.session['username'], name, position, description, location, picture,
                                      timestamp)
        raise cherrypy.HTTPRedirect('/')


    @cherrypy.expose
    @cherrypy.tools.json_in()
    def receiveFile(self):
        ip = cherrypy.request.remote.ip
        fileData = cherrypy.request.json
        if ip in self.rateCounter:
            self.rateCounter[ip] += 1
            if self.rateCounter[ip] > 100:
                print("-----Request rejected, currently being rate limited-----")
                return "11"
            else:
                DatabaseFunctions.add_file_db(fileData['sender'], fileData['destination'],
                                              fileData['filename'],
                                              fileData['stamp'],
                                              fileData['content_type'])
                if self.saveFile(fileData['file'], fileData['filename']):
                    return "0"
                else:
                    return "12"
        else:
            self.rateCounter[ip] = 1
            DatabaseFunctions.add_file_db(fileData['sender'], fileData['destination'],
                                          fileData['filename'],
                                          fileData['stamp'],
                                          fileData['content_type'])
            if self.saveFile(fileData['file'], fileData['filename']):
                return "0"
            else:
                return "12"


    @cherrypy.expose
    def saveFile(self, file, fileName):
        fileInput = base64.b64decode(file)
        f = open("Downloads/" + fileName, "wb+")
        f.write(fileInput)
        f.close()
        if os.path.getsize("Downloads/" + fileName) > (5242880):
            return False
        return True

    @cherrypy.expose
    def sendFile(self, fileData, recipient):
        try:
            sender = cherrypy.session['username']
            destination = recipient
            file = base64.encodestring(fileData.file.read())
            filename = str(fileData.filename)
            content = mimetypes.guess_type(filename, strict=True)
            content_type = content[0]
            stamp = float(time.time())
            if self.saveFile(file, filename):
                destinationIp = DatabaseFunctions.get_ip(recipient)
                destinationPort = DatabaseFunctions.get_port(recipient)

                fileDict = {'sender': sender, 'destination': str(destination), 'file': file,
                            'filename': filename, 'content_type': content_type, 'stamp': stamp}
                fileDict = json.dumps(fileDict)
                url = 'http://' + destinationIp + ":" + destinationPort + '/receiveFile'
                req = urllib2.Request(url, data=fileDict, headers={'content-type': 'application/json'})
                response = urllib2.urlopen(req)
                try:
                    if response.read() == '0':
                        DatabaseFunctions.add_file_db(sender, recipient, filename, stamp, content_type)
                        print("-----File successfully sent-----")
                        raise cherrypy.HTTPRedirect('/showMessages?username={}'.format(recipient))
                except:
                    print("------File failed to send------")
                    raise cherrypy.HTTPRedirect('/showMessages?username={}'.format(recipient))
            else:
                print("-------File exceeds 5Mb-------")
                raise cherrypy.HTTPRedirect('/showMessages?username={}'.format(recipient))
        except KeyError:  # No username
            print("-----User is not logged on-----")
            raise cherrypy.HTTPRedirect("/")


    @cherrypy.expose
    def shutdown(self):
        Details = DatabaseFunctions.get_current_user()
        DatabaseFunctions.drop_current()
        for user in Details:
            self.logoff(user[1], user[2])
        print("===================================")
        print("===SHUTTING DOWN AND LOGGING OFF===")
        print("===================================")


def runMainApp():
    # Create an instance of MainApp and tell Cherrypy to send all requests under / to it. (ie all of them)
    mainObject = MainApp()
    cherrypy.tree.mount(mainObject, "/")

    # Tell Cherrypy to listen for connections on the configured address and port.
    cherrypy.config.update({'server.socket_host': listen_ip,
                            'server.socket_port': listen_port,
                            'engine.autoreload.on': True,
                            })

    cherrypy.quickstart(mainObject, config={
        '/static': {
            'tools.staticdir.root': os.path.abspath(os.getcwd()),
            'tools.staticdir.on': True,
            'tools.staticdir.dir': './static'
        }
    })


    print "========================="
    print "University of Auckland"
    print "COMPSYS302 - Software Design Application"
    print "========================================"

    # Start the web server
    cherrypy.engine.start()

    # And stop doing anything else. Let the web server take over.
    cherrypy.engine.block()


# Run the function to start everything
runMainApp()
