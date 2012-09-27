
from games.objects.basescript import Script

class Linnea(Script):
    def __init__(self, *args, **kwargs):
        # Overriding so people remember to do this on their scripts.
        super(Linnea, self).__init__(*args, **kwargs)

    def activate(self, character):
        activated = True # Successfully activated.

        self.say("There today in order to it activates it knows the letter,"
                 "which it suffered. Fact of jokes of period of training of"
                 "wish of 1 hour.")

        return activated
