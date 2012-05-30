
from random import randint, uniform

from mongoengine_models import Object
from mongoengine_models import IntVector

# Some helpers for random.
def randloc():
    return randint(-100, 100)

def randrot():
    return randint(-360, 360)

def randscale():
    return uniform(.75, 1.25)

class BaseZone(object):
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
        pass
