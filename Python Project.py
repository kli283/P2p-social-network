#!/usr/bin/python
""" cherrypy_example.py

    COMPSYS302 - Software Design
    Author: Andrew Chen (andrew.chen@auckland.ac.nz)
    Last Edited: 19/02/2018

    This program uses the CherryPy web server (from www.cherrypy.org).
"""
# Requires:  CherryPy 3.2.2  (www.cherrypy.org)
#            Python  (We use 2.7)

# The address we listen for connections on
from TestHash import encrypt_string, split_upi

listen_ip = "0.0.0.0"
listen_port = 10001

import cherrypy
import urllib
import sqlite3

connection = sqlite3.connect("UserInfo.db")


class MainApp(object):
    # CherryPy Configuration
    _cp_config = {'tools.encode.on': True,
                  'tools.encode.encoding': 'utf-8',
                  'tools.sessions.on': 'True',
                  }

    # If they try somewhere we don't know, catch it here and send them to the right place.
    @cherrypy.expose
    def default(self, *args, **kwargs):
        """The default page, given when we don't recognise where the request is for."""
        Page = "I don't know where you're trying to go, so have a 404 Error."
        cherrypy.response.status = 404
        return Page

    # PAGES (which return HTML that can be viewed in browser)
    @cherrypy.expose
    def index(self):
        Page = "Welcome! This is a test website for COMPSYS302!<br/>"

        try:
            Page += "Hello " + cherrypy.session['username'] + "!<br/>"
            Page += "Here is some bonus text because you've logged in!" + "!<br/>"
            Page += "Click here to <a href='logout'>logout</a>" + "!<br/>"
            Page += "Click here to view list of users <a href='showUsers'>BAM</a>." + "!<br/>"
            Page += "See who's <a href='showOnline'>ONLINE</a>." + "!<br/>"
            Page += cherrypy.session['username'] + " is Username" + "!<br/>"
            Page += cherrypy.session['password'] + " is Password" + "!<br/>"
        except KeyError:  # There is no username

            Page += "Click here to <a href='login'>login</a>."
        return Page

    @cherrypy.expose
    def login(self):
        Page = '<form action="/signin" method="post" enctype="multipart/form-data">'
        Page += 'Username: <input type="text" name="username"/><br/>'
        Page += 'Password: <input type="password" name="password"/>'
        Page += '<input type="submit" value="Login"/></form>'
        return Page

    @cherrypy.expose
    def logout(self):
        Page = '<form action="/signin" method="post" enctype="multipart/form-data">'
        error = self.logoff(cherrypy.session['username'], cherrypy.session['password'])
        if (error == 0):
            # raise cherrypy.HTTPRedirect('/logoff')
            Page
            Page += cherrypy.session['username'] + " has logged out" + "!<br/>"
        else:
            raise cherrypy.HTTPRedirect('/')
        return Page

    @cherrypy.expose
    def showUsers(self):
        userList = self.listUsers()
        Page = "Here is a list of UPI from COMPSYS302!<br/>"
        for upi in userList:
            Page += upi + "<br/>"
        return Page

    @cherrypy.expose
    def showOnline(self):
        userList = self.listOnline(cherrypy.session['username'], cherrypy.session['password'])
        Page = "Here is a list of people online from COMPSYS302! this is not formatted lol<br/>"
        for user in userList:
            Page += user + "<br/>"
        return Page

    # def showOnline(self):

    @cherrypy.expose
    def sum(self, a=0, b=0):  # All inputs are strings by default
        output = int(a) + int(b)
        return str(output)

    # LOGGING IN AND OUT
    @cherrypy.expose
    def signin(self, username=None, password=None):
        """Check their name and password and send them either to the main page, or back to the main login screen."""
        error = self.reportLogin(username, password, '2', '172.23.128.162', '10001')
        if error == 0:
            cherrypy.session['username'] = username
            cherrypy.session['password'] = encrypt_string(username, password)
            raise cherrypy.HTTPRedirect('/')
        else:
            raise cherrypy.HTTPRedirect('/login')

    # @cherrypy.expose
    # def signout(self, username=cherrypy.session['username'], password=cherrypy.session['password']):
    #     """Logs the current user out, expires their session"""
    #     error = self.logoff(username, password)
    #     if (error == 0):
    #         raise cherrypy.HTTPRedirect('/logoff')
    #     else:
    #         raise cherrypy.HTTPRedirect('/')
    # pass

    # def reportLogin(self, username, password, location, ip, port):
    #     userData = {'username': username, 'password': encrypt_string(username, password), 'location': location,
    #                 'ip': ip, 'port': port}
    #     r = requests.get('http://cs302.pythonanywhere.com/report', params=userData)
    #     returnCode = int(r.text[0:1])
    #     print returnCode
    #     return returnCode
    def reportLogin(self, username, password, location, ip, port):
        userData = urllib.urlencode(
            {'username': username, 'password': encrypt_string(username, password), 'location': location,
             'ip': ip, 'port': port})
        r = urllib.urlopen('http://cs302.pythonanywhere.com/report', userData)

        returnCode = int(r.read()[0:1])
        print returnCode
        return returnCode

    def logoff(self, username, password):
        userData = urllib.urlencode({'username': username, 'password': password})
        r = urllib.urlopen('http://cs302.pythonanywhere.com/logoff', userData)

        returnCode = int(r.read()[0:1])
        print returnCode
        return returnCode

    def listUsers(self):
        r = urllib.urlopen('http://cs302.pythonanywhere.com/listUsers')

        userList = split_upi(r.read())
        print userList
        return userList

    def listOnline(self, username, password):
        userData = urllib.urlencode({'username': username, 'password': password})
        r = urllib.urlopen('http://cs302.pythonanywhere.com/getList', userData)

        userList = split_upi(r.read())
        print userList
        return userList


def runMainApp():
    # Create an instance of MainApp and tell Cherrypy to send all requests under / to it. (ie all of them)
    cherrypy.tree.mount(MainApp(), "/")

    # Tell Cherrypy to listen for connections on the configured address and port.
    cherrypy.config.update({'server.socket_host': listen_ip,
                            'server.socket_port': listen_port,
                            'engine.autoreload.on': True,
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
