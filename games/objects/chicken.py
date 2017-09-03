
from games.objects.basescript import Script


class Chicken(Script):
    def __init__(self, *args, **kwargs):
        # Overriding so people remember to do this on their scripts.
        super(Chicken, self).__init__(*args, **kwargs)

        self.idle_chat = ('BAWK', 'BUCAW', 'BUCK BUCK BUCK', 'BROOOOCK', 'CLUCK')
        self.collide_chat = ("bump.", "bamp!", "BUMP", "THUD!!")

    @classmethod
    def create(cls, number=0):
        obj = ScriptedObject()
        obj.name = "Chicken #%d" % number
        obj.resource = 'chicken'
        obj.loc = (randloc(), randloc(), randloc())
        obj.rot = (randrot(), randrot(), randrot())
        obj.scale = (randscale(), randscale(), randscale())
        obj.vel = (0, 0, 0)
        obj.states.extend(['alive', 'whole', 'clickable'])
        obj.scripts = ['games.objects.chicken']
        obj.save()
        return obj

    def tick(self):
        if self.roll("1d100") == 100:
            self.rand_say(self.idle_chat)

        if self.roll("1d100") == 100:
            # Move around randomly.
            self.say("I think I'll take a stroll!")
            r = self.wander()
            if not r:
                self.rand_say(self.collide_chat)
            else:
                self.say("That stroll was nice.")

