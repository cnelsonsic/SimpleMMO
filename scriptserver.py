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

'''ZoneScriptServer
A server that runs scripts for all the objects in a zone.
This should be started by the ZoneServer.
'''

import threading
from threading import Timer

import sched, time
s = sched.scheduler(time.time, time.sleep)

from settings import CLIENT_UPDATE_FREQ

from basetickserver import BaseTickServer

import mongoengine as me

class ZoneScriptRunner(BaseTickServer):
    '''This is a class that holds all sorts of methods for running scripts for
    a zone. It does not talk to the HTTP handler(s) directly, but instead uses
    the same database. It might take player movement updates directly in the
    future for speed, but this is unlikely.'''

    def __init__(self, zoneid):
        super(ZoneScriptRunner, self).__init__()

        # Make sure mongodb is up
        while True:
            try:
                me.connect(zoneid)
                break
            except(me.connection.ConnectionError):
                # Mongo's not up yet. Give it time.
                time.sleep(.1)

        self.scriptnames = []
        self.scripts = {}

        # Query DB for a list of all objects' script names,
        #   ordered according to proximity to players
        for o in ScriptedObject.objects(scripts__exists):
            # Store list of script names in self
#             self.scriptnames.extend(o.scripts)

            # For each script name in the list:
            for script in o.scripts:
                self.scriptnames[script] = []
                # Import those by name via __import__
                for c in dir(__import__(script)):
                    c()
                    # For each class object in each one's dir()
                    # Instantiate that class.
                    # Store object instance in a dict like {scriptname: classinstance}


    def tick(self):
        '''Iterate through all known scripts and call their tick method.'''
        # Tick all the things
        for script in self.scriptnames:
            # TODO: Pass some locals or somesuch so that they can query the db
            self.scripts[script].tick()


    def start(self):
        print "Running ZoneScript Server."
        super(ZoneScriptRunner, self).start()

if __name__ == "__main__":
    zsr = ZoneScriptRunner()
    zsr.start()
