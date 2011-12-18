#!/usr/bin/env python
'''ZoneServer
A server providing a list of objects present in the zone to clients.
'''

import json
import datetime
import uuid

import tornado
from tornado.web import RequestHandler

from baseserver import BaseServer, SimpleHandler

from tornado.options import define, options

define("port", default=1300, help="Run on the given port.", type=int)
define("zoneid", default='defaultzone', help="Specify what zone to load from disk.", type=int)

class ObjectsHandler(RequestHandler):
    '''ObjectsHandler returns a list of objects and their data.'''

    def get(self):
        self.write(json.dumps(self.get_objects()))

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

        return objects

if __name__ == "__main__":
    handlers = []
    handlers.append((r"/", lambda x, y: SimpleHandler(__doc__, x, y)))
    handlers.append((r"/objects", ObjectsHandler))

    server = BaseServer(handlers)
    server.listen(options.port)

    print "Starting up Zoneserver..."
    server.start()
