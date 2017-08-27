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

from playhouse.shortcuts import model_to_dict

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

from peewee import *

import datetime

from elixir_models import Character, Message, Object, ComplexEncoder, ScriptedObject

from games.objects.basescript import Script


class CharacterController(object):
    '''A controller for mongo character objects.'''
    def __getitem__(self, key):
        return self.get_character(key)

    def get_character(self, character):
        '''Gets a character from the database by name.
        Returns the Character object, or False if it isn't a
        well-formed character object.'''
        try:
            charobj = Object.get_objects(limit=1, player=character)
        except Object.DoesNotExist:
            charobj = False
        return charobj


    def create_character(self, name, owner=""):
        '''Create an in-world character if one does not already exist.
        If one exists, return it.'''
        charobj = self.get_character(name)
        if not charobj:
            # No character in the db named that,
            # So create an object for the player and save it.
            charobj = Object(name=name, owner=owner, states=['player'])
            charobj.save()
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
        charobj = self.get_character(character)
        if charobj:
            return charobj.owner == username
        else:
            return None

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
        charobj.loc_x += xmod * charobj.speed
        charobj.loc_y += ymod * charobj.speed
        charobj.loc_z += zmod * charobj.speed
        charobj.set_modified()

        # Do simple physics here.
        # TODO: Split this into its own method.
        def manhattan(x1, y1, x2, y2):
            return abs(x1-x2) + abs(y1-y2)

        for o in Object.get_objects(physical=True):
            if o.id == charobj.id:
                continue
            # Is the distance between that object and the character less than 3?
            if manhattan(o.loc_x, o.loc_y, charobj.loc_x, charobj.loc_y) < 3:
                # We collided against something, so return now and don't
                # save the location changes into the database.
                return False

        # We didn't collide, hooray!
        # So we'll save to the database and return it.
        charobj.save()
        return charobj

class CharStatusHandler(BaseHandler):
    '''Manages if a character is active in the zone or not.'''

    @tornado.web.authenticated
    def post(self):
        user = self.get_secure_cookie('user')
        character = self.get_argument('character', '')
        status = self.get_argument('status', '')
        self.char_controller = CharacterController()

        # If the character is not owned by this user, disallow it.
#         if not self.char_controller.is_owner(user, character):
#             retval = False

        retval = False
        # Only allow setting the status to online or offline.
        if status in ("online", "offline"):
            if self.char_controller.set_char_status(character, status, user=user):
                retval = True

        self.write(json.dumps(retval))


class MovementHandler(BaseHandler):
    '''A stupid HTTP-based handler for handling character movement.'''
    @tornado.web.authenticated
    def post(self):
        character = self.get_argument('character', '')
        user = self.get_secure_cookie('user')
        self.char_controller = CharacterController()
#         if not self.char_controller.is_owner(user, character):
#             self.set_status(403)
#             self.write("User %s does not own Character %s." % (user, character))
#             return False

        xmod = int(self.get_argument('x', 0))
        ymod = int(self.get_argument('y', 0))
        zmod = int(self.get_argument('z', 0))
        logging.info("Locmod is: %d, %d, %d" % (xmod, ymod, zmod))

        result = self.char_controller.set_movement(character, xmod, ymod, zmod, user=user)

        logging.info("Tried to set movement, result was: %s" % result)

        if result is not False:
            retval = result.json_dumps()
        else:
            retval = json.dumps(result, cls=ComplexEncoder)

        self.content_type = 'application/json'
        self.write(retval)


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

class DateLimitedObjectHandler(BaseHandler):
    '''Gets a list of objects after a certain date.'''
    target_object = None

    def head(self):
        lastdate = Object.get_objects(limit=1).last_modified
        cache_time = 10*365*24*60*60 # 10 Years.
        self.set_header('Last-Modified', lastdate)
        self.set_header('Expires', lastdate + datetime.timedelta(seconds=cache_time))
        self.set_header('Cache-Control', 'max-age=' + str(cache_time))

    @tornado.web.authenticated
    def get(self):
        since = datetime.datetime.strptime(self.get_argument('since', '2010-01-01 00:00:00:000000'), DATETIME_FORMAT)
        if since.year == 2010:
            since = None

        retval = json.dumps([o for o in self.get_objects(since)], cls=ComplexEncoder)
        self.content_type = 'application/json'
        self.write(retval)

    def get_objects(self, since=None):
        '''Gets a list of things from the database.
        Should not be called without an argument except when
        a client connects to the zone initially.'''

        return Object.get_objects(since=since)


class MessageHandler(DateLimitedObjectHandler):
    '''MessageHandler returns a list of messages.'''
    target_object = Message


class ObjectsHandler(DateLimitedObjectHandler):
    '''ObjectsHandler returns a list of objects and their data.'''
    target_object = Object


class ScriptedObjectHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self, object_id):
        character = self.get_argument('character', '')
        retval = self.activate_object(object_id, character)
        if not retval:
            retval = False
        self.write(json.dumps(retval))

    def activate_object(self, object_id, character):
        # Instantiate the scripted object and call its activate thing.
        retval = []
        for o in [Object.get(id=object_id)]:
            # TODO: Break this block into a method.
            for script in o.scripts:
                scriptclass = script.split('.')[-1]
                module = __import__(script, globals(), locals(), [scriptclass], -1)
                # For each entry in the script's dir()
                for key in dir(module):
                    C = getattr(module, key)
                    try:
                        if not issubclass(C, Script):
                            # If it isn't a subclass of Script, skip it.
                            continue
                    except TypeError:
                        # If C isn't a class at all, skip it.
                        continue

                    # Finally activate the script.
                    script_val = C(o).activate(character)
                    if script_val:
                        # Only return it if the script actually returns something.
                        # So clients should only react to activating scripts that
                        # return something meaningful.
                        retval.append(script_val)

        return retval

def main():
    import tornado
    from tornado.options import options, define

    define("dburi", default='testing.sqlite', help="Where is the database?", type=str)

    tornado.options.parse_command_line()

    # Port
    port = options.port
    # Instance Type
    instancetype = options.instancetype
    # Zone name
    zonename = options.zonename
    # Owner
    owner = options.owner


    tornado.options.parse_command_line()
    dburi = options.dburi

    zoneid = '-'.join((instancetype, zonename, owner))
    print "ZoneID: %s" % zoneid

    # Connect to the elixir db
    from elixir_models import setup
    setup(db_uri=dburi)

    print "Loading %s's data." % zonename
    from importlib import import_module
    # Import the zone's init script
    zonemodule = import_module('games.zones.'+zonename)
    # Initialize the zone
    zonescript = zonemodule.Zone(logger=logging.getLogger('zoneserver.'+zoneid))

    handlers = []
    handlers.append((r"/", lambda x, y: SimpleHandler(__doc__, x, y)))
    handlers.append((r"/objects", ObjectsHandler))
    handlers.append((r"/setstatus", CharStatusHandler))
    handlers.append((r"/movement", MovementHandler))
    handlers.append((r"/admin", AdminHandler))
    handlers.append((r"/messages", MessageHandler))
    handlers.append((r"/activate/(.*)", ScriptedObjectHandler))

    server = BaseServer(handlers)
    server.listen(port)

    print "Starting up Zoneserver..."
    server.start()

if __name__ == "__main__":
    main()
