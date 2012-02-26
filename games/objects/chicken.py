
from games.objects.basescript import Script


import random

class Chicken(Script):
    def __init__(self, *args, **kwargs):
        # Overriding so people remember to do this on their scripts.
        super(Chicken, self).__init__(*args, **kwargs)

    def tick(self):
        if random.randint(1, 100) > 95:
            self.say(random.choice(('BAWK', 'BUCAW', 'BUCK BUCK BUCK', 'BROOOOCK', 'CLUCK')))

