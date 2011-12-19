#!/usr/bin/env python
'''CharServer
A server for retrieving information about characters.
For example, getting which zone a character is currently in.
'''

# TODO: Write a function to pull in the docstrings from defined classes here and 
# append them to the module docstring

import json

import tornado
from tornado.web import RequestHandler

from settings import CHARSERVERPORT

from baseserver import BaseServer, SimpleHandler


class CharacterZoneHandler(RequestHandler):
    '''CharacterHandler gets information for a given character.'''

    def get(self, character):
        self.write(json.dumps(self.get_zone(character)))

    def get_zone(self, charname):
        '''Queries the database for information pertaining directly
        to the character.
        It currently only returns the zone the character is in.'''
        return {'zone':'playerinstance-GhibliHills-%s' % (charname,)}

    # TODO: Add character online/offline status

if __name__ == "__main__":
    handlers = []
    handlers.append((r"/", lambda x, y: SimpleHandler(__doc__, x, y)))
    handlers.append((r"/(.*)/zone", CharacterZoneHandler))

    server = BaseServer(handlers)
    server.listen(CHARSERVERPORT)

    print "Starting up Charserver..."
    server.start()
