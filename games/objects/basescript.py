
import datetime

from mongoengine_models import Message

class Script(object):
    '''This is a placeholder class used for doing object script things.
    It's mostly just used for detecting if an object is really a script or not.
    '''
    def __init__(self, mongo_engine_object=None):
        self.me_obj = mongo_engine_object
        print "Initted with %s" % self.me_obj

    def say(self, message):
        '''Write the given text to the zone message database.'''
        Message(sender=self.me_obj.name, body=message, loc=self.me_obj.loc, player_generated=False).save()
        print "[%s] %s: %s" % (datetime.datetime.now(), self.me_obj.name, message)

    def tick(self):
        pass


