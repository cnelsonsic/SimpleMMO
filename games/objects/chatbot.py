
from mongoengine_models import ScriptedObject
from mongoengine_models import IntVector, FloatVector

from games.objects.basescript import Script

class ChatBot(Script):
    idle_chat = ["Try clicking on me.", "Maybe Right Click>Activate?"]
    activation = ['Nice! You activated me.']

    @classmethod
    def create(cls):
        obj = ScriptedObject()
        obj.name = "Linnea"
        obj.resource = 'girl'
        obj.loc = IntVector(x=0, y=0, z=0)
        obj.rot = FloatVector(x=0, y=0, z=0)
        obj.scale = FloatVector(x=1, y=1, z=1)
        obj.vel = FloatVector(x=0, y=0, z=0)
        obj.states.extend(['alive', 'whole', 'clickable'])
        obj.scripts = ['games.objects.chatbot']
        obj.save()
        return obj

    def tick(self):
        if self.roll("1d100") >= 90:
            self.rand_say(self.idle_chat)

    def activate(self, character):
        self.rand_say(self.activation)
        return True

