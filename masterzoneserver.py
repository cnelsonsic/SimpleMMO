#!/usr/bin/env python
'''MasterZoneServer
A server providing URLs to ZoneServers.
'''

import json

import tornado
from tornado.web import RequestHandler

from settings import MASTERZONESERVERPORT

from baseserver import BaseServer, SimpleHandler
from require_basic_auth import require_basic_auth


class ZoneHandler(RequestHandler):
    '''ZoneHandler gets the URL for a given zone ID, or spins up a new 
    instance of the zone for that player.'''

    def get(self, zoneid):
        self.write(self.get_url(zoneid))

    def get_url(self, zoneid):
        '''Gets the zone URL from the database based on its id.
        ZoneServer ports start at 1300.'''
        return 'http://localhost:1300/'

if __name__ == "__main__":
    handlers = []
    handlers.append((r"/", lambda x, y: SimpleHandler(__doc__, x, y)))
    handlers.append((r"/(.*)", ZoneHandler))

    server = BaseServer(handlers)
    server.listen(MASTERZONESERVERPORT)

    print "Starting up Master Zoneserver..."
    server.start()
