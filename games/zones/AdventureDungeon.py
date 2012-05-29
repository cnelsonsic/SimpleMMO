
from mongoengine_models import Object, ScriptedObject
from mongoengine_models import IntVector, FloatVector


class Zone(object):
    def __init__(self):
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

    def insert_objects(self):
        # Linnea is checked for in unit tests.
        obj = ScriptedObject()
        obj.name = "Linnea"
        obj.resource = 'npc-girl'
        obj.loc = IntVector(x=0, y=0, z=0)
        obj.rot = FloatVector(x=0, y=0, z=0)
        obj.scale = FloatVector(x=0, y=0, z=0)
        obj.vel = FloatVector(x=0, y=0, z=0)
        obj.scripts = ['games.objects.linnea']
        obj.save()


