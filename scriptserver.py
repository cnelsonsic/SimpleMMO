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
This is started by the MasterZoneServer when its sibling ZoneServer is started.
'''

import time
import logging
logger = logging.getLogger('ScriptServer')
hdlr = logging.FileHandler('log/scriptserver.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)


import mongoengine as me

from mongoengine_models import ScriptedObject, Message, Object
from games.objects.basescript import Script

from settings import CLIENT_UPDATE_FREQ, MAX_ZONE_OBJECT_MESSAGE_COUNT

from basetickserver import BaseTickServer

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

        # While the zone is not loaded, wait.
        while not Object.objects(name="Loading Complete."):
            time.sleep(.1)

        self.load_scripts()
        logger.info("Started with data for zone: %s" % zoneid)

    def load_scripts(self):
        '''(Re)Load scripts for objects in this zone.'''
        self.scripts = {}

        # Query DB for a list of all objects' script names,
        #   ordered according to proximity to players
        logger.info(ScriptedObject.objects)
        for o in ScriptedObject.objects(scripts__exists=True):
            logger.info("Scripted Object: {0}".format(o.name))
            # Store list of script names in self

            # For each script name in the list:
            for script in o.scripts:
                logger.info("Importing %s" % script)
                if script not in self.scripts:
                    self.scripts[script] = []

                # Import those by name via __import__
                scriptclass = script.split('.')[-1]
                module = __import__(script, globals(), locals(), [scriptclass], -1)
                # For each entry in the script's dir()
                for key in dir(module):
                    C = getattr(module, key)

                    try:
                        if not issubclass(C, Script):
                            # If it isn't a subclass of Script, continue.
                            continue
                    except TypeError:
                        # If C isn't a class at all, continue.
                        continue

                    # No sense in instantiating the default Script instance.
                    if C != Script:
                        # Store object instance in a list.
                        self.scripts[script].append(C(mongo_engine_object=o))


    def tick(self):
        '''Iterate through all known scripts and call their tick method.'''
        # Tick all the things
        for scriptname, scripts in self.scripts.items():
            for script in scripts:
                logger.info("Ticking {0}".format(script))
                # TODO: Pass some locals or somesuch so that they can query the db
                script.tick()

        # Clean up mongodb's messages by deleting all but the most recent 100 non-player messages
        for m in Message.objects(player_generated=False).order_by('-sent')[MAX_ZONE_OBJECT_MESSAGE_COUNT:]:
            logger.info("Deleting message from %s" % m.sent.time())
            m.delete()

    def start(self):
        logger.info("Running ZoneScript Server.")
        super(ZoneScriptRunner, self).start()

if __name__ == "__main__":
    import sys
    zoneid = sys.argv[1] if len(sys.argv) > 1 else "playerinstance-defaultzone-None"
    zsr = ZoneScriptRunner(zoneid)
    zsr.start()
