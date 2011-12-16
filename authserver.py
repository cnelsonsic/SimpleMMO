#!/usr/bin/env python

class AuthServer(object):
    '''AuthServer authenticates a user and redirects them to the appropriate ZoneServer.'''

    def authenticate(self, username, password):
        '''Compares a username/password pair against that in the database.
        If they match, return True.
        Else, return False.'''

    def get_zoneserver(self, character):
        '''Takes a character reference and gets the zoneserver that they should
        be redirected to.
        Returns a URL for that zoneserver.'''

