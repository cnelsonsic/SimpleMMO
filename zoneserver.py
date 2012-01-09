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

zoneid = options.zoneid
print zoneid

bind = DataStore('mongodb://localhost:27017/', database=zoneid)
SESSION = Session(bind)

class Object(Document):
    '''In-world objects.'''
    class __mongometa__:
        session = SESSION
        name = 'object'

    _id = Field(schema.ObjectId)
    name = Field(str)
    resource = Field(str)
    loc = Field(dict(x=int, y=int, z=int))
    rot = Field(dict(x=int, y=int, z=int)) # Could be a quaternion.
    scale = Field(dict(x=float, y=float, z=float))
    vel = Field(dict(x=float, y=float, z=float))
    states = Field([str])
    active = Field(bool)

# Make sure mongodb is up
while True:
    try:
        objects = Object.m.find().first()
        print objects
        break
    except(ming.exc.MongoGone):
        # Mongo's not up yet. Give it time.
        time.sleep(.1)
        print "sleeping"

class ObjectsHandler(BaseHandler):
    '''ObjectsHandler returns a list of objects and their data.'''

    @tornado.web.authenticated
    def get(self):
        self.write(json.dumps(self.get_objects(), default=json_util.default))

    def get_objects(self):
        '''Gets a list of objects in the zone.
        Uses cacheing, and should not be called except when a client 
        connects to the zone initially'''
        cache_time = 10*365*24*60*60 # 10 Years.

        self.set_header('Last-Modified', datetime.datetime.utcnow())
        self.set_header('Expires', datetime.datetime.utcnow() + datetime.timedelta(seconds=cache_time))
        self.set_header('Cache-Control', 'max-age=' + str(cache_time))

        objects = [
                    {
                        'id': str(uuid.uuid4()),
                        'resource': 'barrel',
                        'name': 'Barrel',
                        'loc': (4, 6, 34),
                        'rot': (45, 90, 0),
                        'scale': (1, 1, 0.9),
                        'vel': (0, 0, 0),
                        'states': ('closed', 'whole', 'clickable'),
                    }
                  ]

        import time; time.sleep(4) # Simulate high server usage to make caching more obvious

        # Query the mongo objects database
        objects = Object.m.find().all()
        print objects

        return objects


class CharStatusHandler(BaseHandler):
    '''Manages if a character is active in the zone or not.'''

    @tornado.web.authenticated
    def post(self):
        character = self.get_argument('character', '')
        status = self.get_argument('status', '')
        # If user owns this character
        return self.set_status(character, status)

    def set_status(self, character, status):
        '''Sets a character's online status.'''
        # Set the character's status in the zone's database.
        return True


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
    print len(Object.m.find().all())
    if len(Object.m.find().all()) == 0:
        # Insert some test data.
        print "Inserting test data."
        from helpers import coord_dictify as _
        obj = Object({
                'name': 'Barrel',
                'resource': 'barrel',
                'loc': _(4, 6, 34),
                'rot': _(45, 90, 0),
                'scale': _(1, 1, 0.9),
                'vel': _(0, 0, 0),
                'states': ['closed', 'whole', 'clickable'],
                })
        obj.m.save()
        assert len(Object.m.find().all()) == 1

    print "Starting up Zoneserver..."
    server.start()

if __name__ == "__main__":
    main(port=options.port, zoneid=options.zoneid)
