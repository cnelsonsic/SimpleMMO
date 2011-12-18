#!/usr/bin/env python
'''AuthServer
A server providing authentication, and allows a user to get a list of their characters.
'''

# TODO: Write a function to pull in the docstrings from defined classes here and 
# append them to the module docstring

import json

import tornado
from tornado.web import RequestHandler

from settings import AUTHSERVERPORT

from baseserver import BaseServer, SimpleHandler
from require_basic_auth import require_basic_auth

class PingHandler(RequestHandler):
    def get(self):
        self.write("pong")

@require_basic_auth
class AuthHandler(RequestHandler):
    '''AuthHandler authenticates a user and sets a session in the database.'''

    def get(self, basicauth_user, basicauth_pass):
        self.authenticate(basicauth_user, basicauth_pass)
        # TODO: Write a sessionId to the database and return it

    def post(self, **kwargs):
        basicauth_user = kwargs['basicauth_user']
        basicauth_pass = kwargs['basicauth_pass']

    def authenticate(self, username, password):
        '''Compares a username/password pair against that in the database.
        If they match, return True.
        Else, return False.'''
        return True

@require_basic_auth
class CharacterHandler(RequestHandler):
    '''CharacterHandler gets a list of characters for the given user account.'''

    def get(self, basicauth_user, basicauth_pass):
        self.write(json.dumps(self.get_characters(basicauth_user)))

    def post(self, **kwargs):
        basicauth_user = kwargs['basicauth_user']
        basicauth_pass = kwargs['basicauth_pass']

    def get_characters(self, username):
        '''Queries the database for all characters owned by a particular username.'''
        return ['Graxnor', 'Rumtiddlykins']

if __name__ == "__main__":
    handlers = []
    handlers.append((r"/", lambda x, y: SimpleHandler(__doc__, x, y)))
    handlers.append((r"/ping", PingHandler))
    handlers.append((r"/authenticate", AuthHandler))
    handlers.append((r"/characters", CharacterHandler))

    server = BaseServer(handlers)
    server.listen(AUTHSERVERPORT)

    print "Starting up Authserver..."
    server.start()
