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

import logging
import tornado

import json

from elixir_models import User, Character

from settings import CHARSERVERPORT

from baseserver import BaseServer, SimpleHandler, BaseHandler

class CharacterZoneHandler(BaseHandler):
    '''CharacterZoneHandler gets zone information for a given character.'''

    def get(self, character):
        self.write(json.dumps(self.get_zone(character)))
        self.set_header('Content-Type', 'application/json')

    def get_zone(self, charname):
        '''Queries the database for information pertaining directly
        to the character.
        It currently only returns the zone the character is in.'''
        return {'zone':'playerinstance-GhibliHills-%s' % (charname,)}

    # TODO: Add character online/offline status

class CharacterCreationHandler(BaseHandler):
    '''CharacterHandler handles character creation.'''

    @tornado.web.authenticated
    def post(self):
        character_name = self.get_argument("character_name")
        character_name = self.create(character_name)
        if character_name is False:
            # Creating the character was prohibited.
            raise tornado.web.HTTPError(400, 'Character already exists.')
        elif not character_name:
            # Creating the character failed outright.
            raise tornado.web.HTTPError(400, 'Creating character failed.')

        self.write(character_name)

    def create(self, character_name):
        logging.info("Creating a character named %s" % character_name)
        try:
            user = User.get(username=self.get_current_user())
        except User.DoesNotExist:
            return

        if Character.select().where(Character.name==character_name).exists():
            return False

        character = Character(user=user, name=character_name)
        character.save()
        logging.info("Created a character %s" % character)
        return character.name

if __name__ == "__main__":
    handlers = []
    handlers.append((r"/", lambda x, y: SimpleHandler(__doc__, x, y)))
    handlers.append((r"/new", CharacterCreationHandler))
    handlers.append((r"/(.*)/zone", CharacterZoneHandler))

    server = BaseServer(handlers)
    server.listen(CHARSERVERPORT)

    print "Starting up Charserver..."
    try:
        server.start()
    except KeyboardInterrupt:
        logging.info("Exiting Charserver.")
