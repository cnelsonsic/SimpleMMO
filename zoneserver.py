#!/usr/bin/env python
'''ZoneServer
A server providing a list of objects present in the zone to clients.
'''

import json
import datetime
import uuid
import time

import tornado

from baseserver import BaseServer, SimpleHandler, BaseHandler

# from ming_models import *

from tornado.options import define, options
try:
    from tornado.websocket import WebSocketHandler
except(ImportError):
    print "Couldn't import WebSocketHandler."
    WebSocketHandler = BaseHandler

define("port", default=1300, help="Run on the given port.", type=int)
define("zoneid", default='defaultzone', help="Specify what zone to load from disk.", type=str)

from pymongo import json_util
import ming
from ming import Session
from ming import Field, schema
from ming.declarative import Document
from ming.datastore import DataStore

import mongoengine as me

tornado.options.parse_command_line()
zoneid = options.zoneid
print zoneid

bind = DataStore('mongodb://localhost:27017/', database=zoneid)
SESSION = Session(bind)

# Make sure mongodb is up
while True:
    try:
        me.connect(zoneid)
        break
    except(me.connection.ConnectionError):
        # Mongo's not up yet. Give it time.
        time.sleep(.1)
        print "sleeping"

class IntVector(me.EmbeddedDocument):
    '''A document for holding documents with three integer vectors: 
        x, y and z.'''
    x = me.IntField(default=0)
    y = me.IntField(default=0)
    z = me.IntField(default=0)

class FloatVector(me.EmbeddedDocument):
    '''A document for holding documents with three float vectors:
        x, y and z.'''
    x = me.FloatField(default=0)
    y = me.FloatField(default=0)
    z = me.FloatField(default=0)

class Object(me.Document):
    '''In-world objects.'''
    name = me.StringField(default="")
    resource = me.StringField(default="")

    loc = me.EmbeddedDocumentField(IntVector)
    rot = me.EmbeddedDocumentField(FloatVector)
    scale = me.EmbeddedDocumentField(FloatVector)
    vel = me.EmbeddedDocumentField(FloatVector)

    states = me.ListField(me.StringField())
    active = me.BooleanField(default=True)
    last_modified = me.DateTimeField(default=datetime.datetime.now)



class ObjectsHandler(BaseHandler):
    '''ObjectsHandler returns a list of objects and their data.'''

    @tornado.web.authenticated
    def get(self):
        since = self.get_argument('since', None)
        objs = [m.to_mongo() for m in self.get_objects(since)]
        retval = json.dumps(objs, default=json_util.default)
        self.write(retval)

    def get_objects(self, since=None):
        '''Gets a list of objects in the zone.
        Uses cacheing, and should not be called without an argument except when
        a client connects to the zone initially.'''
        cache_time = 10*365*24*60*60 # 10 Years.

        self.set_header('Last-Modified', datetime.datetime.utcnow())
        self.set_header('Expires', datetime.datetime.utcnow() + datetime.timedelta(seconds=cache_time))
        self.set_header('Cache-Control', 'max-age=' + str(cache_time))

#         import time; time.sleep(4) # Simulate high server usage to make caching more obvious

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
        character = self.get_argument('character', '')
        status = self.get_argument('status', '')
        # If user owns this character
        if status in ("online", "offline"):
            return self.set_char_status(character, status)
        return False

    def set_char_status(self, character, status):
        '''Sets a character's online status.'''
        # Set the character's status in the zone's database.
        try:
            charobj = Object.objects(name=character)[0]
        except(IndexError):
            # No character named that.
            # So create an object for the player and save it.
            charobj = Object()
            charobj.name = character
            charobj.states.append('player')

        if status not in charobj.states:
            charobj.states.append(status)

        # Remove any mutually exclusive character states except what was passed.
        for s in ('online', 'offline'):
            if s != status:
                if s in charobj.states:
                    charobj.states.remove(s)

        charobj.states = list(set(charobj.states)) # Remove any duplicates.
        charobj.save()

        return charobj


class MovementHandler(BaseHandler):
    '''A stupid HTTP-based handler for handling character movement.'''
    @tornado.web.authenticated
    def post(self):
        character = self.get_argument('character', '')
        xmod = self.get_argument('x', 0)
        ymod = self.get_argument('y', 0)
        zmod = self.get_argument('z', 0)

        self.set_movement(character, xmod, ymod, zmod)
        return True

    def set_movement(self, character, xmod, ymod, zmod):
        pass
        # Set the character's new position based on the x, y and z modifiers.

# TODO: A char movmeent handler token handler, which gives the user a token to use.
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
            self.set_movement(m['char'], m['x'], m['y'], m['z'])
        
        self.write_message("ok")

    def set_movement(self, character, xmod, ymod, zmod):
        pass
        # Set the character's new position based on the x, y and z modifiers.


def main(port=1300, zoneid="defaultzone"):
    handlers = []
    handlers.append((r"/", lambda x, y: SimpleHandler(__doc__, x, y)))
    handlers.append((r"/objects", ObjectsHandler))
    handlers.append((r"/setstatus", CharStatusHandler))
    handlers.append((r"/movement", MovementHandler))

    server = BaseServer(handlers)
    server.listen(port)

    # If no objects in database:
    print len(Object.objects)
    if len(Object.objects) == 0:
        # Insert some test data.
        print "Inserting test data."
        from helpers import coord_dictify as _
        obj = Object()
        obj.name ='Barrel'
        obj.resource = 'barrel'
        obj.loc = IntVector(x=4, y=6, z=34)
        obj.rot = FloatVector(x=45, y=90, z=0)
        obj.scale = FloatVector(x=1, y=1, z=.9)
        obj.vel = FloatVector(x=0, y=0, z=0)
        obj.states.extend(['closed', 'whole', 'clickable'])
        obj.save()
        assert len(Object.objects) == 1

    print "Starting up Zoneserver..."
    server.start()

if __name__ == "__main__":
    main(port=options.port, zoneid=options.zoneid)
