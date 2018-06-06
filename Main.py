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
    # Initialises thread for rate limiting and auto login
    enableThread = {}
    rateCounter = {}
    # Initialises the database
    DatabaseFunctions.create_database()
    # Initialises the current user logged on, for multiple users
    DatabaseFunctions.init_current_user()

    # Gets current directory
    CUR_DIR = os.path.dirname(os.path.abspath(__file__))
    # Initialises Jinja2 environment
    env = Environment(
        loader=FileSystemLoader(CUR_DIR),
        trim_blocks=True,
        # This line will sanitise unwanted scripts with Jinja2
        autoescape=select_autoescape(['html'])
    )

    # The function to logout is called here once the server is stopped.
    def __init__(self):
        cherrypy.engine.subscribe('stop', self.shutdown)
        thread = threading.Thread(target=self.threadRate)
        thread.daemon = True
        thread.start()

    # Rate Limiting function
    def rateCount(self):
        print("-----User is blocked, too many requests-----")
        return "11"

    # If they try somewhere we don't know, catch it here and send them to the right place.
    @cherrypy.expose
    def default(self, *args, **kwargs):
        """The default page, given when we don't recognise where the request is for."""
        Page = "I don't know where you're trying to go, so have a 404 Error."
        cherrypy.response.status = 404
        return Page

    # This is the function that initialises the page of the user when navigating to the home page
    @cherrypy.expose
    def index(self):
        # Initialises the current user if they have not been already and and initialises the templates for Jinja2
        DatabaseFunctions.init_current_user()
        template = self.env.get_template('index.html')
        loginTemplate = self.env.get_template('login.html')

        try:
            # The rest of this function passes information of the user and other details to be passed into HTML
            userList = self.listUsers()
            userDictionary = self.showOnline()
            onlineUsers = []
            user = cherrypy.session['username']
            try:
                profileDetails = DatabaseFunctions.get_user_profile(user)
                # A check is done in case it is the first time a user logs on, if it is then the profile will be
                # set to a default value so that something is able to be passed into HTML
                if len(profileDetails) == 0:
                    DatabaseFunctions.add_profile(cherrypy.session['username'], "none", "none", "none", "none", "none",
                                                  float(time.time()))
                    profileDetails = DatabaseFunctions.get_user_profile(cherrypy.session['username'])
                try:
                    updateTime = time.strftime("%d-%m-%Y %I:%M %p", time.localtime(float(profileDetails[0][7])))
                except:
                    updateTime = "Time for last updated is not available"
            except:
                DatabaseFunctions.add_profile(cherrypy.session['username'], "none", "none", "none", "none", "none",
                                              float(time.time()))
                profileDetails = DatabaseFunctions.get_user_profile(cherrypy.session['username'])
            for userNum in userDictionary:
                onlineUsers.append(userDictionary[str(userNum)]['username'])
            # These are then rendered using Jinja2
            return template.render(user=user, userList=userList, profile=profileDetails, time=updateTime)
        except KeyError:  # No username
            print("-----User is not logged on-----")
            return loginTemplate.render()

    # This function returns the login page
    @cherrypy.expose
    def login(self):
        return file("login.html")  # OR urllib.urlopen("index.html").read()

    # This function handles the return value for logging off to see whether or not it is successful
    @cherrypy.expose
    def logout(self):
        # Page = '<form action="/signin" method="post" enctype="multipart/form-data">'
        error = self.logoff(cherrypy.session['username'], cherrypy.session['password'])
        if (error == 0):
            cherrypy.session.clear()
            raise cherrypy.HTTPRedirect('/')
        else:
            raise cherrypy.HTTPRedirect('/')

    # This function gets the details for all the messages between two users and renders it to HTML
    @cherrypy.expose
    def showMessages(self, username=None):
        # Checks for online users to prepare the values to send into HTML
        try:
            if username is None:
                # Checks if there is an actual user logged on
                username = cherrypy.session['username']
            user = cherrypy.session['username']
            userDictionary = self.showOnline()
        except KeyError:  # No user is logged on
            print("-----User is not logged on-----")
            raise cherrypy.HTTPRedirect("/")
        # Initialises the template
        template = self.env.get_template('Message.html')
        myPic = DatabaseFunctions.get_user_profile(user)
        # Fetches the profile pictures of both users from the database
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
            # Renders all the details to HTML with Jinja2
            return template.render(title='Messages', messages=convo, profilePic=friendPic, otherPic=myPic,
                                   onlineUsers=userDictionary, user=user, sender=recipient)
        except:
            print("-----Problems with reading message. Other user may have encryption-----")

    # This function loads HTML onto the page to give the user the ability to send files
    @cherrypy.expose
    def showFile(self):
        try:
            # The function sendFile is called with the button press
            Page = '<form action="/sendFile" method="post" enctype="multipart/form-data">'
            Page += 'Select file: <input type="file" name="fileData" ><br/>'
            Page += 'Receiver: <input type="text" name="recipient"/><br/>'
            Page += '<input type="submit" value="Send"/></form>'
            # This page will also show users that are online
            userDictionary = self.showOnline()
            Page += "Here is a list of people online from COMPSYS302!<br/>"
            Page += "Number of users online: " + str(len(userDictionary)) + " <br/><br/>"
            for userNum in userDictionary:
                Page += userDictionary[str(userNum)]['username'] + " <br/>"
            return Page
        except KeyError:  # No user is logged on
            print("-----User is not logged on-----")
            raise cherrypy.HTTPRedirect("/")

    # This function sends a request to the login server and then returns the json of everyone currently logged
    # onto the server
    @cherrypy.expose
    @cherrypy.tools.json_in()
    def showOnline(self):
        userData = urllib.urlencode(
            {'username': cherrypy.session['username'], 'password': cherrypy.session['password']})
        r = urllib.urlopen('http://cs302.pythonanywhere.com/getList?&enc=0&json=1', userData)
        userDictionary = r.read()
        userDictionary = json.loads(userDictionary)
        # The details are also stored onto the database
        DatabaseFunctions.add_online_db(userDictionary)
        return userDictionary

    # This function passes in the username password and location to then check whether the user
    # successfully logs in or not
    @cherrypy.expose
    def signin(self, username, password, location):
        # The ip and port are acquired first
        local_ip = self.getIp()
        port = listen_port
        DatabaseFunctions.add_current_user(username, encrypt_string(username, password), location)
        # Check their name and password and send them either to the main page, or back to the main login screen
        error = self.reportLogin(username, password, location, local_ip, port)
        if error == 0:
            cherrypy.session['username'] = username
            cherrypy.session['password'] = encrypt_string(username, password)
            # A thread is started to make sure that the login is reported regularly to the login server
            thread = threading.Thread(target=self.threadLogin, args=(username, password, location))
            self.enableThread[username] = True
            thread.daemon = True
            thread.start()
            raise cherrypy.HTTPRedirect('/')
        else:
            print("------Error logging in------")
            raise cherrypy.HTTPRedirect('/login')

    # This is the threading function that constantly calls the reportLogin function every 30 seconds
    @cherrypy.expose
    def threadLogin(self, username, password, location):
        ip = self.getIp()
        port = DatabaseFunctions.get_port(username)
        while self.enableThread[username]:
            self.reportLogin(username, password, location, ip, port)
            print "-----Reporting Login-----"
            time.sleep(30)

    # This is the threading function that is used as a 1 minute timer for rate limiting
    @cherrypy.expose
    def threadRate(self):
        while True:
            print "-----Rate limiting timer-----"
            self.rateCounter.clear()
            time.sleep(60)

    # This function sends a request to the login server and returns an error code to determine whether the login
    # is a success or not
    def reportLogin(self, username, password, location, ip, port):
        userData = urllib.urlencode(
            {'username': username, 'password': encrypt_string(username, password), 'location': location,
             'ip': ip, 'port': port})
        r = urllib.urlopen('http://cs302.pythonanywhere.com/report', userData)
        returnCode = int(r.read()[0:1])
        return returnCode

    # This function acquires the IP address of the current user
    def getIp(self):
        s = socket.socket(socket.AF_INET,
                          socket.SOCK_DGRAM)  # Code from https://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        # public_ip was used when testing outside of the university because the code above did not get the right IP
        public_ip = urllib.urlopen('http://ip.42.pl/raw').read()  # Was used when testing with port forwarding
        return ip

    # This function sends a request to the login server and returns an error code to determine if the user
    # has successfully logged off or not
    @cherrypy.expose
    def logoff(self, username, password):
        userData = urllib.urlencode({'username': username, 'password': password})
        r = urllib.urlopen('http://cs302.pythonanywhere.com/logoff', userData)
        self.enableThread[username] = False
        DatabaseFunctions.drop_current_user(username)
        returnCode = int(r.read()[0:1])
        return returnCode

    # This function sends a request to the login server to read all the users on the server
    def listUsers(self):
        r = urllib.urlopen('http://cs302.pythonanywhere.com/listUsers')
        userList = split_upi(r.read())
        # The values are also added onto the database
        DatabaseFunctions.add_upi_db(userList)
        return userList

    # This function is called when the user needs to ping another user and returns the error code of the other user
    # being pinged
    @cherrypy.expose
    def pingUser(self, username, IP, port):
        request = urllib2.Request('http://' + IP + ":" + port + '/ping?sender=' + username)
        response = urllib2.urlopen(request, timeout=0.8)
        errorCode = response.read()
        return errorCode[0]

    # This function is called when another user tries to ping the current user
    @cherrypy.expose
    def ping(self, sender):
        ip = cherrypy.request.remote.ip
        # The rate is to be limited to 100 counts per ip
        if ip in self.rateCounter:
            self.rateCounter[ip] += 1
            if self.rateCounter[ip] > 100:
                # The function to return the rate limit error code
                return self.rateCount()
            else:
                return "0"
        else:
            self.rateCounter[ip] = 1
            return "0"

    # This function is called when another user wishes to send the current user a message
    @cherrypy.expose
    @cherrypy.tools.json_in()
    def receiveMessage(self):
        ip = cherrypy.request.remote.ip
        # The rate is to be limited to 100 counts per ip
        if ip in self.rateCounter:
            self.rateCounter[ip] += 1
            if self.rateCounter[ip] > 100:
                # The function to return the rate limit error code
                return self.rateCount()
            else:
                # Organising data then calling a function to add everything to the database
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

    # This is the function that sends the message. It would first try to see whether the recipient is online,
    # then send the message.
    @cherrypy.expose
    def sendMessage(self, recipient, message):
        try:
            # Finds the time, ip and port
            currentTime = float(time.time())
            destinationIp = DatabaseFunctions.get_ip(recipient)
            destinationPort = DatabaseFunctions.get_port(recipient)
            try:
                # Pings the other user, and if it returns 0 then get the information, otherwise print an error
                # to state that the message is unsuccesfully sent
                pingCode = self.pingUser(cherrypy.session['username'], destinationIp, destinationPort)
                messageDict = {"sender": cherrypy.session['username'], "message": message, "destination": recipient,
                               "stamp": currentTime}
                messageDict = json.dumps(messageDict)
            except:
                print("------Message failed to send, unable to ping recipient------")
                raise cherrypy.HTTPRedirect('/showMessages?username={}'.format(recipient))
            # If the user can be pinged, send a request to send the message to the other user
            if pingCode == '0':
                url = 'http://' + destinationIp + ":" + destinationPort + '/receiveMessage'
                req = urllib2.Request(url, data=messageDict, headers={'content-type': 'application/json'})
                response = urllib2.urlopen(req)
                # The other user's response is then checked
                if response.read() == '0':
                    DatabaseFunctions.add_msg_db(cherrypy.session['username'], recipient, message, currentTime)
                    print("-----Message successfully sent-----")
                    raise cherrypy.HTTPRedirect('/showMessages?username={}'.format(recipient))
                else:
                    print("------Message failed to send, no response code from recipient------")
                    raise cherrypy.HTTPRedirect('/showMessages?username={}'.format(recipient))
        except KeyError:  # No user is logged on
            print("-----User is not logged on-----")
            raise cherrypy.HTTPRedirect("/")

    # This function returns the profile for the current user to the other user trying to make a request
    @cherrypy.expose
    @cherrypy.tools.json_in()
    def getProfile(self):
        ip = cherrypy.request.remote.ip
        input_data = cherrypy.request.json
        UPI = input_data["profile_username"]
        # The data is fetched from the database, then organised
        profile = DatabaseFunctions.get_user_profile(UPI)
        output_dict = {"lastUpdated": profile[0][7], "fullname": profile[0][2],
                       "position": profile[0][3], "description": profile[0][4],
                       "location": profile[0][5], "picture": profile[0][6]}
        output_dict = json.dumps(output_dict)
        # Rate limiting below, see above for more thorough explaination
        if ip in self.rateCounter:
            self.rateCounter[ip] += 1
            if self.rateCounter[ip] > 100:
                return self.rateCount()
            else:
                return output_dict
        else:
            self.rateCounter[ip] = 1
            return output_dict

    # This function acquires the desired user's profile and adds it to the database
    @cherrypy.expose
    def acquireProfile(self, userProfile):
        postdata = {'profile_username': userProfile, 'sender': cherrypy.session['username']}
        destinationIp = DatabaseFunctions.get_ip(userProfile)
        destinationPort = DatabaseFunctions.get_port(userProfile)
        try:
            url = 'http://' + destinationIp + ":" + destinationPort + '/getProfile?'
            data = json.dumps(postdata)
            req = urllib2.Request(url, data=data, headers={'content-type': 'application/json'})
            response = urllib2.urlopen(req, timeout=1)
            response = response.read()
            profileDict = json.loads(response)
            # Organising the data that has been acquired
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

    # This function passes in the user profile and passes on information to HTML to render the profile page
    @cherrypy.expose
    def requestProfile(self, userProfile):
        try:
            # Initialises the template
            template = self.env.get_template('Profile.html')
            error = ""
            try:
                # Acquires the user's details
                destinationIp = DatabaseFunctions.get_ip(userProfile)
                destinationPort = DatabaseFunctions.get_port(userProfile)
                try:
                    pingCode = self.pingUser(cherrypy.session['username'], destinationIp, destinationPort)
                    if pingCode == '0':
                        self.acquireProfile(userProfile)
                except:
                    print("-----Something went wrong trying to acquire profile-----")
            except:
                error += "user does not exist"
                print("-----User does not exist-----")
            userList = self.listUsers()
            try:
                profile = DatabaseFunctions.get_user_profile(userProfile)
            except:
                # Returns the profile for the current user that is logged on
                error += "No profile available"
                userProfile = DatabaseFunctions.get_current_user()
                userProfile = userProfile[0][1]
                profile = DatabaseFunctions.get_user_profile(userProfile)
            try:
                updateTime = time.strftime("%d-%m-%Y %I:%M %p", time.localtime(float(profile[0][7])))
            except:
                updateTime = "Time for last updated is not available"
            try:
                # Renders the page to HTML
                return template.render(user=userProfile, userList=userList, profile=profile, time=updateTime,
                                       error=error)
            except:
                raise cherrypy.HTTPRedirect('/')
        except KeyError:  # No user is logged on
            print("-----User is not logged on-----")
            raise cherrypy.HTTPRedirect("/")

    # This function returns HTML to give the user the ability to make changes to their profile
    @cherrypy.expose
    def editProfile(self):
        try:
            currentUser = cherrypy.session['username']
            profile = DatabaseFunctions.get_user_profile(currentUser)
            # The data acquired from the data base is organised
            UPI = profile[0][1]
            name = profile[0][2]
            position = profile[0][3]
            description = profile[0][4]
            location = profile[0][5]
            picture = profile[0][6]
            Page = UPI + " this is your profile! <br/>"
            Page += '<img src=' + picture + ' alt="Profile picture" style = "max-width: 500px; max-height: 500px">'
            Page += "<br/> " + "Full Name: " + name + " <br/>"
            Page += "Position " + position + " <br/>"
            Page += "Full Description: " + description + " <br/>"
            Page += "Location: " + location + " <br/>"
            # All the input boxes have been made required to be filled in
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

    # This function is called too save the profile information into the database
    @cherrypy.expose
    def saveProfile(self, name, position, description, location, picture):
        timestamp = float(time.time())
        DatabaseFunctions.add_profile(cherrypy.session['username'], name, position, description, location, picture,
                                      timestamp)
        raise cherrypy.HTTPRedirect('/')

    # This function is called when the user is to receive a file from another user
    @cherrypy.expose
    @cherrypy.tools.json_in()
    def receiveFile(self):
        ip = cherrypy.request.remote.ip
        fileData = cherrypy.request.json
        # Rate limiting, see above for a more detailed explanation
        if ip in self.rateCounter:
            self.rateCounter[ip] += 1
            if self.rateCounter[ip] > 100:
                return self.rateCount()
            else:
                # The file details are added to the database
                DatabaseFunctions.add_file_db(fileData['sender'], fileData['destination'],
                                              fileData['filename'],
                                              fileData['stamp'],
                                              fileData['content_type'])
                # The actual file is then saved by calling the saveFile function
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

    # This function saves the file being passed into it and returns true or false depending on if the file
    # is less than 5Mb or not
    @cherrypy.expose
    def saveFile(self, file, fileName):
        # The file is first decoded then saved
        fileInput = base64.b64decode(file)
        f = open("Downloads/" + fileName, "wb+")
        f.write(fileInput)
        f.close()
        if os.path.getsize("Downloads/" + fileName) > (5242880):
            return False
        return True

    # This function is called when the user wishes to send a file to another user
    @cherrypy.expose
    def sendFile(self, fileData, recipient):
        try:
            sender = cherrypy.session['username']
            destination = recipient
            # The file is encrypted then the file type is found
            file = base64.encodestring(fileData.file.read())
            filename = str(fileData.filename)
            content = mimetypes.guess_type(filename, strict=True)
            content_type = content[0]
            stamp = float(time.time())
            # The file is then saved and if it is valid, a request will be made to the other user to send the file
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
                    # If there is no response from the other user, the following error message will display
                    print("------File failed to send------")
                    raise cherrypy.HTTPRedirect('/showMessages?username={}'.format(recipient))
            else:
                print("-------File exceeds 5Mb-------")
                raise cherrypy.HTTPRedirect('/showMessages?username={}'.format(recipient))
        except KeyError:  # No user is logged in
            print("-----User is not logged on-----")
            raise cherrypy.HTTPRedirect("/")

    # This function is called to automatically log off the users when the server shuts down
    @cherrypy.expose
    def shutdown(self):
        Details = DatabaseFunctions.get_current_user()
        # A loop is used to log off each user active in the system
        for user in Details:
            self.logoff(user[1], user[2])
        DatabaseFunctions.drop_current()
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
    # The configuration for the static folder
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
