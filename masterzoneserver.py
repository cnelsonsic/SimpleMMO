#!/usr/bin/env python
'''MasterZoneServer
A server providing URLs to ZoneServers.
'''

import json
from subprocess import Popen

import tornado
from tornado.web import RequestHandler

from settings import MASTERZONESERVERPORT, PROTOCOL, HOSTNAME

from baseserver import BaseServer, SimpleHandler

ZONEPID = None

class ZoneHandler(RequestHandler):
    '''ZoneHandler gets the URL for a given zone ID, or spins up a new 
    instance of the zone for that player.'''

    @tornado.web.authenticated
    def get(self, zoneid):
        # Check that the authed user owns that zoneid in the database.
        self.write(self.get_url(zoneid))

    def get_url(self, zoneid):
        '''Gets the zone URL from the database based on its id.
        ZoneServer ports start at 1300.'''
        return self.launch_zone('playerinstance', 'GhibliHills', 'Groxnor')

    def launch_zone(self, instance_type, name, owner):
        '''Starts a zone given the type of instance, name and character that owns it.
        Returns the zone URL for the new zone server.'''
        # Query the database for an unused zone port.
        port = 1300
        # Make sure the instance type is allowed
        # Make sure the name exists
        # Make sure owner is real
        # Try to start a zone server
        p = Popen(' '.join(['/usr/bin/python', 'zoneserver.py', '--port %d' % port, '&']), shell=True)
        ZONEPID = p.pid

        # If successful, write our URL to the database and return it
        return ''.join((PROTOCOL, '://', HOSTNAME, ':', str(port), '/'))

if __name__ == "__main__":
    handlers = []
    handlers.append((r"/", lambda x, y: SimpleHandler(__doc__, x, y)))
    handlers.append((r"/(.*)", ZoneHandler))

    server = BaseServer(handlers)
    server.listen(MASTERZONESERVERPORT)

    print "Starting up Master Zoneserver..."
    server.start()
