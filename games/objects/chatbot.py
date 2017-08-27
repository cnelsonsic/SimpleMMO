
from elixir_models import Object
from games.objects.basescript import Script

class ChatBot(Script):
    idle_chat = ["Try clicking on me.", "Maybe Right Click>Activate?"]
    activation = ['Nice! You activated me.']

    @classmethod
    def create(cls):
        obj = Object()
        obj.name = "Linnea"
        obj.resource = 'girl'
        obj.loc_x, obj.loc_y, obj.loc_z = 0, 0, 0
        obj.rot_x, obj.rot_y, obj.rot_z = 0, 0, 0
        obj.scale_x, obj.scale_y, obj.scale_z = 0, 0, 0
        obj.vel_x, obj.vel_y, obj.vel_z = 0, 0, 0
        obj.states.extend(['alive', 'whole', 'clickable'])
        obj.scripts = ['games.objects.chatbot']
        obj.save()
        return obj

    def tick(self):
        if self.roll("1d100") >= 90:
            self.rand_say(self.idle_chat)
        self.wander()

    def activate(self, character):
        self.rand_say(self.activation)
        return True

