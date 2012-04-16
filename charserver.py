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

'''CharServer
A server for retrieving information about characters.
For example, getting which zone a character is currently in.
'''

# TODO: Write a function to pull in the docstrings from defined classes here and 
# append them to the module docstring

import json

from settings import CHARSERVERPORT

from baseserver import BaseServer, SimpleHandler, BaseHandler

class CharacterZoneHandler(BaseHandler):
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
    import tornado
    from tornado.options import options, define
    define("dburi", default='sqlite:///simplemmo.sqlite', help="Where is the database?", type=str)

    tornado.options.parse_command_line()
    dburi = options.dburi

    # Connect to the elixir db
    from elixir_models import setup
    setup(db_uri=dburi)

    handlers = []
    handlers.append((r"/", lambda x, y: SimpleHandler(__doc__, x, y)))
    handlers.append((r"/(.*)/zone", CharacterZoneHandler))

    server = BaseServer(handlers)
    server.listen(CHARSERVERPORT)

    print "Starting up Charserver..."
    server.start()
