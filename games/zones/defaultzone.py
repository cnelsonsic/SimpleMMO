# This file is imported when the zone wants to load an instance of this zone.

from random import randint, uniform

from mongoengine_models import Object, ScriptedObject
from mongoengine_models import IntVector, FloatVector

# Some helpers for random.
def randloc():
    return randint(-100, 100)

def randrot():
    return randint(-360, 360)

def randscale():
    return uniform(.75, 1.25)

class Zone(object):
    def __init__(self):
        '''Initialize the zone.
        Insert whatever objects into the database programmatically.
        This includes loading things from a disk file if you so choose.

        It will not run more than once on the zone's database.
        If you want new content on an existing database, either make
        a script to apply changes, or just delete the database for
        that zone and recreate it when the zone is started up again.
        '''

        if not self.is_loaded():
            self.insert_objects()
            # Loading complete.
            self.set_loaded()

    def is_loaded(self):
        return True if Object.objects(name="Loading Complete.") else False

    def set_loaded(self):
        from sys import maxint

        obj = Object()
        obj.name = "Loading Complete."
        far = maxint*-1
        obj.loc = IntVector(x=far, y=far, z=far)
        obj.states.extend(['hidden'])
        obj.save()
        print obj.name

    def insert_objects(self):
        '''Insert any objects you want to be present in the zone into the
        database in this call.

        This gets called exactly once per database. If you change something here
        and want it to appear in the zone's database, you will need to clear the
        database first.

        Deleting the "Loading Complete" object will only cause duplicates.
        Do not do this.
        '''

        # Place 100 barrels randomly:
        for i in xrange(100):
            obj = Object()
            obj.name = "Barrel%d" % i
            obj.resource = 'barrel'
            obj.loc = IntVector(x=randloc(), y=randloc(), z=randloc())
            obj.rot = FloatVector(x=randrot(), y=randrot(), z=randrot())
            obj.scale = FloatVector(x=randscale(), y=randscale(), z=randscale())
            obj.vel = FloatVector(x=0, y=0, z=0)
            obj.states.extend(['closed', 'whole', 'clickable'])
            obj.save()

        # Place 10 chickens randomly:
        for i in xrange(10):
            obj = ScriptedObject()
            obj.name = "Chicken #%d" % i
            obj.resource = 'chicken'
            obj.loc = IntVector(x=randloc(), y=randloc(), z=randloc())
            obj.rot = FloatVector(x=randrot(), y=randrot(), z=randrot())
            obj.scale = FloatVector(x=randscale(), y=randscale(), z=randscale())
            obj.vel = FloatVector(x=0, y=0, z=0)
            obj.states.extend(['alive', 'whole', 'clickable'])
            obj.scripts = ['games.objects.chicken']
            obj.save()

        print [o.name for o in Object.objects()]

