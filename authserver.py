#!/usr/bin/env python
'''AuthServer
A server providing authentication, and allows a user to get a list of their characters.
'''

# TODO: Write a function to pull in the docstrings from defined classes here and 
# append them to the module docstring

import json

import tornado

from settings import AUTHSERVERPORT

from baseserver import BaseServer, SimpleHandler, BaseHandler
from require_basic_auth import require_basic_auth

class PingHandler(BaseHandler):
    def get(self):
        self.write("pong")

class AuthHandler(BaseHandler):
    '''AuthHandler authenticates a user and sets a session in the database.'''
    def post(self):
        username = self.get_argument("username", "")
        password = self.get_argument("password", "")
        auth = self.authenticate(username, password)
        if auth:
            self.set_current_user(username)
            self.write('Login successful.')
        else:
            self.write('Login Failed, username and/or password incorrect.')
            raise tornado.web.HTTPError(401)

    def authenticate(self, username, password):
        '''Compares a username/password pair against that in the database.
        If they match, return True.
        Else, return False.'''
        # Do some database stuff here to verify the user.
        return True

    def set_current_user(self, user):
        if user:
            self.set_secure_cookie("user", user)
        else:
            self.clear_cookie("user")

class LogoutHandler(BaseHandler):
    '''Unsets the user's cookie.'''
    def get(self):
        self.clear_cookie("user")

class CharacterHandler(BaseHandler):
    '''CharacterHandler gets a list of characters for the given user account.'''

    @tornado.web.authenticated
    def get(self):
        self.write(json.dumps(self.get_characters(self.get_current_user())))

    def get_characters(self, username):
        '''Queries the database for all characters owned by a particular username.'''
        return ['Graxnor', 'Rumtiddlykins']

if __name__ == "__main__":
    handlers = []
    handlers.append((r"/", lambda x, y: SimpleHandler(__doc__, x, y)))
    handlers.append((r"/ping", PingHandler))
    handlers.append((r"/login", AuthHandler))
    handlers.append((r"/logout", LogoutHandler))
    handlers.append((r"/characters", CharacterHandler))

    server = BaseServer(handlers)
    server.listen(AUTHSERVERPORT)

    print "Starting up Authserver..."
    server.start()
