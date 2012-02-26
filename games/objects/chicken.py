
from games.objects.basescript import Script

import random
import datetime

class Chicken(Script):
    def __init__(self, *args, **kwargs):
        # Overriding so people remember to do this on their scripts.
        super(Chicken, self).__init__(*args, **kwargs)

    def tick(self):
        if self.roll("1d100") == 100:
            self.say(random.choice(('BAWK', 'BUCAW', 'BUCK BUCK BUCK', 'BROOOOCK', 'CLUCK')))

        if self.roll("1d100") == 100:
            # Move around randomly.
            self.say("I think I'll take a stroll!")
            self.me_obj.loc.x += random.randint(-1, 1)
            self.me_obj.loc.y += random.randint(-1, 1)
            self.me_obj.set_modified()

