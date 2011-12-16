#!/usr/bin/env python

class ZoneServer(object):
    '''ZoneServer manages sending location, rotation, velocity information about
        world objects to the client.

        Could spin up a tiny WebSocket server per client
        that wants to update their loc/rot/vel remotely.
        Or use Tornado and just use its websocket handler.
        '''

    def get_obj_info(self, obj):
        '''Get an objects location, rotation, and velocity.'''

    def get_objects(self):
        '''Returns ALL objects in this zone.'''
