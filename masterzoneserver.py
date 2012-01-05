#!/usr/bin/env python
'''MasterZoneServer
A server providing URLs to ZoneServers.
'''

import json
import time
import multiprocessing
from subprocess import Popen

import tornado

from settings import MASTERZONESERVERPORT, PROTOCOL, HOSTNAME

from baseserver import BaseServer, SimpleHandler, BaseHandler
import zoneserver

ZONEPIDS = []
NEXTCLEANUP = time.time()+(5*60)

JOBS = []

class ZoneHandler(BaseHandler):
    '''ZoneHandler gets the URL for a given zone ID, or spins up a new 
    instance of the zone for that player.'''

    @tornado.web.authenticated
    def get(self, zoneid):
        self.cleanup()
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
#         pname = ''.join((instance_type, name, owner))
#         p = multiprocessing.Process(name=pname, target=zoneserver.main, args=(port,))
#         p.daemon = True
#         JOBS.append(p)
#         print "Starting %s as PID %d on port %d." % (pname, p.pid, port)
#         p.start()

        zoneid = ''.join((instance_type, name, owner))

        p = Popen(' '.join(['/usr/bin/python', 'zoneserver.py', '--port=%d' % port, '--zoneid=%s' % zoneid, '&']), shell=True)
        ZONEPIDS.append(p.pid)

        # Wait for server to come up
        # Or just query it on "/" every hundred ms or so.
        zoneurl = ''.join((PROTOCOL, '://', HOSTNAME, ':', str(port)))
        import time
        time.sleep(1)

        # If successful, write our URL to the database and return it
        return zoneurl

    def cleanup(self):
        # Every 5 minutes...
        global NEXTCLEANUP
        if NEXTCLEANUP < time.time():
            NEXTCLEANUP = time.time()+(5*60)
            for pid in PIDS:
                pass
                # If pid not in database
                    # Kill the process by pid

if __name__ == "__main__":
    handlers = []
    handlers.append((r"/", lambda x, y: SimpleHandler(__doc__, x, y)))
    handlers.append((r"/(.*)", ZoneHandler))

    server = BaseServer(handlers)
    server.listen(MASTERZONESERVERPORT)

    print "Starting up Master Zoneserver..."
    server.start()
