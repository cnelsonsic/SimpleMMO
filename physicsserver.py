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

'''PhysicsServer
A server that runs a physics simulation for all the objects in a zone.
It doesn't really care why or how objects ended up where they claim to be now.
It pretends to be a client with omniscient control over all the little
puppets, er, I mean movable Objects in the zone.
It determines if an object can occupy the space it claims to be in now,
and if not, it fixes it.
Think of it as a physics-based position sanity check.

This should be started by the ZoneServer.
'''

from uuid import uuid4

import mongoengine as me
from mongoengine_models import Object

import pymunk as pm
from pymunk import Vec2d
### Physics collision types
COLLTYPE_BALL = 2

from settings import CLIENT_UPDATE_FREQ

from basetickserver import BaseTickServer

class PhysicsServer(BaseTickServer):
    '''This class is responsible for simulating all the physics in the zone.'''

    def __init__(self, zoneid):
        super(PhysicsServer, self).__init__()
        self.zoneid = zoneid

        # Make sure mongodb is up
        while True:
            try:
                me.connect(zoneid)
                break
            except(me.connection.ConnectionError):
                # Mongo's not up yet. Give it time.
                time.sleep(.1)

        print "Started with data for zone: %s" % zoneid

        # Set up a PyMunk scene for our simulation.
        self.space = pm.Space()
        self.space.gravity = Vec2d(0.0, 0.0)
#         self.space.damping = 0.5
#         self.space.idleSpeedThreshold = 1.0
#         self.space.sleepTimeThreshold = 0.05
        self.objects = [] # All the pymunk shapes in the scene.

        # Query DB for a full list of all objects' physical "descriptions".
        mass = 10
        radius = 100
        moment = pm.moment_for_circle(mass, 0, radius, (0,0))
        for o in Object.objects(): # FIXME: Only get physical objects!
            # Update our internal scene with it.
            body = pm.Body(mass, moment)
            body.position = o.loc['x'], o.loc['y']
            shape = pm.Circle(body, radius, (0,0))
            shape.friction = 0.7
            shape.collision_type = COLLTYPE_BALL
            self.space.add(body, shape)
            body.me_obj = o
            self.objects.append(body)

    def tick(self):
        '''Get any updated objects in the scene since the last tick,
        and update their position in the physics simulation.
        Step the sim forward a bit and see what got jostled out of place.
        Then update the database with any objects that have changed positions.'''
        self.update_scene()
        self.step()
        self.update_database()

    def update_scene(self):
        '''Update the internal scene with any changes to the zone's objects.
        This is like get_objects() from the client, only directly grabbing from the server.'''

    def step(self):
        '''Step the scene simulation forward until we're satisfied.'''
        dt = 1.0/60.0
        for shape in self.space.shapes:
            if shape.body.is_sleeping:
                continue
            for x in range(100):
                self.space.step(dt)

    def update_database(self):
        '''Send any changes we made to our internal scene to the database,
        so that any movement or bumping or jostling is persisted into the zone.'''
#         from pprint import pprint
#         pprint({o.me_obj.id:o.position for o in self.objects})
        for o in self.objects:
            x, y = o.position
            o.me_obj.loc['x'] = x
            o.me_obj.loc['y'] = y
            o.me_obj.set_modified()

    def start(self):
        print "Running PhysicsServer."
        super(PhysicsServer, self).start()

if __name__ == "__main__":
    import sys
    zoneid = sys.argv[1] if len(sys.argv) > 1 else "playerinstance-defaultzone-None"
    ps = PhysicsServer(zoneid)
    ps.start()
