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
'''

import threading
from threading import Timer

import sched, time
s = sched.scheduler(time.time, time.sleep)

from settings import CLIENT_UPDATE_FREQ

from basetickserver import BaseTickServer

class ZoneScriptRunner(BaseTickServer):
    '''This is a class that holds all sorts of methods for running scripts for
    a zone. It does not talk to the HTTP handler(s) directly, but instead uses
    the same database. It might take player movement updates directly in the
    future for speed, but this is unlikely.
    This should be started by the ZoneServer.'''

    def __init__(self):
        super(ZoneScriptRunner, self).__init__()

        self.scriptnames = []
        self.scripts = {}

        # Query DB for a list of all objects' script names,
        #   ordered according to proximity to players
        # Store list of script names in self
        # For each script name in the list:
        #   Import those by name via __import__
        #   For each class object in each one's dir()
        #       call class()
        #       store object instance in a dict like {scriptname: classinstance}

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
