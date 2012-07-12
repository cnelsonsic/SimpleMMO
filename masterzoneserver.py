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

import time
import logging

import tornado
import requests

from settings import MASTERZONESERVERPORT, PROTOCOL, HOSTNAME, ZONESTARTUPTIME,\
                     START_ZONE_WITH, SUPERVISORD, SUBPROCESS

from baseserver import BaseServer, SimpleHandler, BaseHandler

NEXTCLEANUP = time.time()+(5*60)

JOBS = []

from elixir_models import session, Zone
logging.getLogger('connectionpool').setLevel(logging.ERROR)

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
        logging.info("Launching zone %s" % zoneid)
        instance_type, name, owner = zoneid.split("-")
        return self.launch_zone(instance_type, name, owner)

    def launch_zone(self, instance_type, name, owner):
        '''Starts a zone given the type of instance, name and character that owns it.
        Returns the zone URL for the new zone server.'''
        # Make sure the instance type is allowed
        # Make sure the name exists
        # Make sure owner is real

        zoneid = '-'.join((instance_type, name, owner))

        # If it's in the database, it's probably still up:
        zone = Zone.get_by(zoneid=zoneid)
        if zone and zone.url:
            logging.info("Got zone url %s for zoneid %s from database." % (zone.url, zoneid))
            return zone.url

        # See if it's already up:
        zones = Zone.query.filter_by(zoneid=zoneid).all()
#         from settings import PROTOCOL, HOSTNAME
        serverurl = None
        for zone in zones:
            port = zone.port
            serverurl = zone.url
#             serverurl = "%s://%s:%d" % (PROTOCOL, HOSTNAME, port.port)
            try:
                status = requests.get(serverurl).status_code
                if status == 200:
                    logging.info("Server was already up and in the db: %s" % serverurl)
                    break
            except (requests.ConnectionError, requests.URLRequired):
                serverurl = None
                continue


        # Server is not already up
        if not serverurl:
            # Try to start a zone server
            if START_ZONE_WITH == SUPERVISORD:
                logging.info("Starting process with supervisord.")
                from start_supervisord_process import start_zone
                try:
                    serverurl = start_zone(zonename=name, instancetype=instance_type, owner=owner)
                except UserWarning, exc:
                    if "Zone already exists in process list." in exc:
                        print exc
                        logging.info("Zone is already up.")
                        pass
                    else:
                        raise

            elif START_ZONE_WITH == SUBPROCESS:
                logging.info("Starting process with subprocess.")
                from start_subprocess import start_zone, start_scriptserver
                z, serverurl = start_zone(zonename=name, instancetype=instance_type, owner=owner)
                s = start_scriptserver(zonename=name, instancetype=instance_type, owner=owner)
                JOBS.extend([z, s])

        # Wait for server to come up
        # Just query it on "/" every hundred ms or so.
        starttime = time.time()
        status = 0
        numrequests = 0
        logging.info("Waiting for server on %s" % serverurl)
        while status != 200:
            try:
                status = requests.get(serverurl).status_code
                numrequests += 1
            except(requests.ConnectionError):
                # Not up yet...
                pass

            time.sleep(.1)
            if time.time() > starttime+ZONESTARTUPTIME:
                logging.info("ZoneServer never came up after %d seconds." % ZONESTARTUPTIME)
                raise tornado.web.HTTPError(504, "Launching zone %s timed out." % serverurl)

        logging.info("Starting zone %s (%s) took %f seconds and %d requests." % (zoneid, serverurl, time.time()-starttime, numrequests))
        print "Starting zone %s (%s) took %f seconds and %d requests." % (zoneid, serverurl, time.time()-starttime, numrequests)

        # If successful, write our URL to the database and return it
        # Store useful information in the database.
        logging.info(serverurl)
        Zone(zoneid=zoneid, port=serverurl.split(":")[-1], owner=owner, url=serverurl)
        session.commit()
        logging.info("Zone server came up at %s." % serverurl)
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

    import tornado
    from tornado.options import options, define
    define("dburi", default='sqlite:///simplemmo.sqlite', help="Where is the database?", type=str)

    tornado.options.parse_command_line()
    dburi = options.dburi

    # Connect to the elixir db
    from elixir_models import setup
    setup(db_uri=dburi)

    # On startup, iterate through entries in zones table. See if they are up, if not, delete them.
    for port in [z[0] for z in session.query(Zone.port).all()]:
        serverurl = "%s://%s:%d" % (PROTOCOL, HOSTNAME, port)
        try:
            requests.get(serverurl)
        except(requests.ConnectionError):
            # Server is down, remove it from the zones table.
            Zone.query.filter_by(port=port).delete(), Zone
        session.commit()

    server = BaseServer(handlers)
    server.listen(MASTERZONESERVERPORT)

    print "Starting up Master Zoneserver..."
    try:
        server.start()
    except KeyboardInterrupt:
        # Catch ctrl+c and continue with the script.
        pass

    for job in JOBS:
        job.terminate()
