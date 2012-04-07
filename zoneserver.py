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
'''ZoneServer
A server providing a list of objects present in the zone to clients.
'''

import json
import datetime
import time
import logging

import tornado

from baseserver import BaseServer, SimpleHandler, BaseHandler

from settings import DATETIME_FORMAT

from tornado.options import define, options
try:
    from tornado.websocket import WebSocketHandler
except(ImportError):
    print "Couldn't import WebSocketHandler."
    WebSocketHandler = BaseHandler

define("port", default=1300, help="Run on the given port.", type=int)
define("zonename", default='defaultzone', help="Specify what zone to load from disk.", type=str)
define("instancetype", default='playerinstance', help="Specify what type of zone this is.", type=str)
define("owner", default='None', help="Specify who owns this zone.", type=str)

from pymongo import json_util

import mongoengine as me

from mongoengine_models import Character, Object, IntVector

class CharacterController(object):
    '''A controller for mongo character objects.'''
    def __getitem__(self, key):
        return self.get_character(key)

    def get_character(self, character):
        '''Gets a character from the database by name.
        Returns the Character object, or False if it isn't a
        well-formed character object.'''
        try:
            charobj = Character.objects(name=character).first()
            return charobj if charobj.states else False
        except(IndexError, AttributeError):
            return False

    def create_character(self, name, owner=""):
        '''Create an in-world character if one does not already exist.
        If one exists, return it.'''
        # TODO: This is pretty dumb and needs reorganized.
        charobj = self.get_character(name)
        if not charobj:
            # No character in the db named that,
            # So create an object for the player and save it.
            charobj = Character()
            charobj.name = name
            charobj.owner = owner
            charobj.states.append('player')
        return charobj

    def set_char_status(self, character, status, user=None):
        '''Sets a character's online status.'''

        # Get or Create this character.
        charobj = self.create_character(character, owner=user)

        # does the character already have this status?
        if status not in charobj.states:
            # If not, we need to append it.
            charobj.states.append(status)

        # Remove any mutually exclusive character states except what was passed.
        for s in ('online', 'offline'):
            # If the status we're trying to set is not the one we're currently on
            # and the status we're iterating on is in the character states already.
            if status != s and s in charobj.states:
                charobj.states.remove(s)

        # Remove any duplicate states
        charobj.states = list(set(charobj.states))

        charobj.save()

        return charobj

    def is_owner(self, username, character):
        charobj = Character.objects(name=character).first()
        if charobj:
            return charobj.owner == username
        else:
            return False

    def set_movement(self, character, xmod, ymod, zmod, user=None):
        charobj = self.create_character(character, owner=user)

#         try:
#             charobj.loc
#         except(AttributeError):
#             # Character doesn't exist, create a new one.
#             self.set_status(500)
#             self.write('Character "%s" was not set to online, and didn\'t exist in the database.' % character)
#             return

        # Set the character's new position based on the x, y and z modifiers.
        if hasattr(charobj, 'loc'):
            charobj.loc['x'] += xmod*charobj.speed
            charobj.loc['y'] += ymod*charobj.speed
            charobj.loc['z'] += zmod*charobj.speed
            charobj.last_modified = datetime.datetime.now()
        else:
            charobj.loc = IntVector(x=0, y=0, z=0)

        # Do simple physics here.
        # TODO: Split this into its own method.
        def manhattan(x1, y1, x2, y2):
            return abs(x1-x2) + abs(y1-y2)

        charx, chary = charobj.loc['x'], charobj.loc['y']
        for o in Object.objects(physical=True):
            # Is the distance between that object and the character less than 3?
            if manhattan(o.loc['x'], o.loc['y'], charx, chary) < 3:
                # We collided against something, so return now and don't
                # save the location changes into the database.
                return False

        # We didn't collide, hooray!
        # So we'll save to the database and return it.
        charobj.save()
        return charobj


class ObjectsHandler(BaseHandler):
    '''ObjectsHandler returns a list of objects and their data.'''

#     @tornado.web.authenticated
    def head(self):
        lastdate = Object.objects.order_by('-last_modified').first().last_modified
        cache_time = 10*365*24*60*60 # 10 Years.
        self.set_header('Last-Modified', lastdate)
        self.set_header('Expires', lastdate + datetime.timedelta(seconds=cache_time))
        self.set_header('Cache-Control', 'max-age=' + str(cache_time))

    @tornado.web.authenticated
    def get(self):
        since = datetime.datetime.strptime(self.get_argument('since', '2010-01-01 00:00:00:000000'), DATETIME_FORMAT)
        if since.year == 2010:
            since = None
        objs = [m.to_mongo() for m in self.get_objects(since)]
        retval = json.dumps(objs, default=json_util.default)
        self.content_type = 'application/json'
        self.write(retval)

    def get_objects(self, since=None):
        '''Gets a list of objects in the zone.
        Should not be called without an argument except when
        a client connects to the zone initially.'''

        # Query the mongo objects database
        if since is not None:
            objects = Object.objects(last_modified__gte=since)
        else:
            objects = Object.objects

        return objects


class CharStatusHandler(BaseHandler):
    '''Manages if a character is active in the zone or not.'''

    @tornado.web.authenticated
    def post(self):
        user = self.get_secure_cookie('user')
        character = self.get_argument('character', '')
        status = self.get_argument('status', '')
        self.char_controller = CharacterController()

        if not self.char_controller.is_owner(user, character):
            return False

        # Only allow setting the status to online or offline.
        if status in ("online", "offline"):
            return self.char_controller.set_char_status(character, status, user=user)
        return False


class MovementHandler(BaseHandler):
    '''A stupid HTTP-based handler for handling character movement.'''
    @tornado.web.authenticated
    def post(self):
        character = self.get_argument('character', '')
        user = self.get_secure_cookie('user')
        self.char_controller = CharacterController()
        if not self.char_controller.is_owner(user, character):
            self.set_status(403)
            self.write("User %s does not own Character %s." % (user, character))
            return False

        xmod = int(self.get_argument('x', 0))
        ymod = int(self.get_argument('y', 0))
        zmod = int(self.get_argument('z', 0))
        logging.info("Locmod is: %d, %d, %d" % (xmod, ymod, zmod))

        return self.char_controller.set_movement(character, xmod, ymod, zmod, user=user)


# TODO: A char movement handler token handler, which gives the user a token to use.
class WSMovementHandler(WebSocketHandler):
    '''This is a sample movement handler, which really should be replaced with
    something a bit more efficient and/or featureful.'''

    def open(self):
        print "WebSocket opened"

        self.receive_message(self.on_message)

    def on_message(self, message):
        print message
        m = json.loads(message)
        user = self.get_secure_cookie('user')
        command = m['command']
        if command == "mov":
            self.set_movement(m['char'], m['x'], m['y'], m['z'], user=user)

        self.write_message("ok")

    def set_movement(self, character, xmod, ymod, zmod):
        pass
        # Set the character's new position based on the x, y and z modifiers.

class AdminHandler(BaseHandler):

    def __init__(self, *args, **kwargs):
        super(AdminHandler, self).__init__(*args, **kwargs)

        self.commands = {'echo': self.echo}

    def echo(self, arg):
        return arg

    @tornado.web.authenticated
    def post(self):
        if self.get_secure_cookie('admin') == 'true':
            command = self.get_argument('command', '')
            args = json.loads(self.get_argument('args', ''))
            if command in self.commands:
                return self.commands['command'](*args)
        else:
            raise tornado.web.HTTPError(403)


def main(port=1300):
    tornado.options.parse_command_line()

    # Instance Type
    instancetype = options.instancetype
    # Zone name
    zonename = options.zonename
    # Owner
    owner = options.owner

    zoneid = '-'.join((instancetype, zonename, owner))
    print "ZoneID: %s" % zoneid

    # Make sure mongodb is up
    while True:
        try:
            me.connect(zoneid)
            break
        except(me.connection.ConnectionError):
            # Mongo's not up yet. Give it time.
            time.sleep(.1)
            print "sleeping"

    print "Loading %s's data." % zonename
    from importlib import import_module
    # Import the zone's init script
    zonemodule = import_module('games.zones.'+zonename)
    # Initialize the zone
    zonescript = zonemodule.Zone()

    handlers = []
    handlers.append((r"/", lambda x, y: SimpleHandler(__doc__, x, y)))
    handlers.append((r"/objects", ObjectsHandler))
    handlers.append((r"/setstatus", CharStatusHandler))
    handlers.append((r"/movement", MovementHandler))
    handlers.append((r"/admin", AdminHandler))

    server = BaseServer(handlers)
    server.listen(port)

    print "Starting up Zoneserver..."
    server.start()

if __name__ == "__main__":
    main(port=options.port)
