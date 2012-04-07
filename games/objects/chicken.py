
from games.objects.basescript import Script

class Chicken(Script):
    def __init__(self, *args, **kwargs):
        # Overriding so people remember to do this on their scripts.
        super(Chicken, self).__init__(*args, **kwargs)

        self.idle_chat = ('BAWK', 'BUCAW', 'BUCK BUCK BUCK', 'BROOOOCK', 'CLUCK')
        self.collide_chat = ("bump.", "bamp!", "BUMP", "THUD!!")

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

