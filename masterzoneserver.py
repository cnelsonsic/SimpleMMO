#!/usr/bin/env python
# ##### BEGIN AGPL LICENSE BLOCK #####
# This file is part of SimpleMMO.
#
# Copyright (C) 2011, 2012  Charles Nelson
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ##### END AGPL LICENSE BLOCK #####

'''MasterZoneServer
A server providing URLs to ZoneServers.
'''

import json
import time
import logging

import tornado
import requests

from settings import MASTERZONESERVERPORT, PROTOCOL, HOSTNAME, ZONESTARTUPTIME,\
                        ZONESTARTPORT, ZONEENDPORT

from baseserver import BaseServer, SimpleHandler, BaseHandler

ZONEPIDS = []
NEXTCLEANUP = time.time()+(5*60)

JOBS = []

from elixir_models import *

# On startup, iterate through entries in zones table. See if they are up, if not, delete them.
for port in [z[0] for z in session.query(Zone.port).all()]:
    serverurl = "%s://%s:%d" % (PROTOCOL, HOSTNAME, port)
    try:
        requests.get(serverurl)
    except(requests.ConnectionError):
        # Server is down, remove it from the zones table.
        Zone.query.filter_by(port=port).delete()
    session.commit()

class ZoneHandler(BaseHandler):
    '''ZoneHandler gets the URL for a given zone ID, or spins up a new 
    instance of the zone for that player.'''

    @tornado.web.authenticated
    def get(self, zoneid):
        self.cleanup()
        # Check that the authed user owns that zoneid in the database.
        try:
            self.write(self.get_url(zoneid))
        except UserWarning, exc:
            if "timed out." in exc:
                raise tornado.web.HTTPError(504, exc)

    def get_url(self, zoneid):
        '''Gets the zone URL from the database based on its id.
        ZoneServer ports start at 1300.'''
        instance_type, name, owner = zoneid.split("-")
        return self.launch_zone(instance_type, name, owner)

    def launch_zone(self, instance_type, name, owner):
        '''Starts a zone given the type of instance, name and character that owns it.
        Returns the zone URL for the new zone server.'''
        # Make sure the instance type is allowed
        # Make sure the name exists
        # Make sure owner is real

        # Try to start a zone server
        pname = ''.join((instance_type, name, owner))
        from start_supervisord_process import start_zone
        try:
            serverurl = start_zone(zonename=name, instancetype=instance_type, owner=owner)
        except(UserWarning), exc:
            if "Zone already exists in process list." in exc:
                # Zone is already up
                pass
            else:
                raise


        # Wait for server to come up
        # Or just query it on "/" every hundred ms or so.
        import time
        starttime = time.time()
        status = 0
        numrequests = 0
        while status != 200:
            try:
                status = requests.get(serverurl).status_code
                numrequests += 1
            except(requests.ConnectionError):
                # Not up yet...
                pass

            time.sleep(.1)
            if time.time() > starttime+ZONESTARTUPTIME:
                raise UserWarning("Launching zone %s timed out." % serverurl)

        print "Starting zone %s (%s) took %f seconds and %d requests." % (pname, serverurl, time.time()-starttime, numrequests)

        # If successful, write our URL to the database and return it
        # TODO: Store useful information in the database.
        return serverurl

    def cleanup(self):
        # Every 5 minutes...
        global NEXTCLEANUP
        if NEXTCLEANUP < time.time():
            NEXTCLEANUP = time.time()+(5*60)
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
