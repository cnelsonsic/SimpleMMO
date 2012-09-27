
import datetime

from mongoengine_models import Message

import re
import random

from settings import MAX_DICE_AMOUNT
from mongoengine_models import Object

def parse(s):
    result = re.search(r'^((?P<rolls>\d+)#)?(?P<dice>\d*)d(?P<sides>\d+)(?P<mod>[+-]\d+)?$', s)
    return (result.group('rolls') or 0,
            result.group('dice') or 1,
            result.group('sides') or 2,
            result.group('mod') or 0)

class Script(object):
    '''This is a placeholder class used for doing object script things.
    It's mostly just used for detecting if an object is really a script or not.
    '''
    def __init__(self, mongo_engine_object=None):
        self.me_obj = mongo_engine_object
        print "Initted with %s" % self.me_obj

    def create(self):
        '''Create this Script's ScriptedObject database object.'''
        pass

    def activate(self, *args, **kwargs):
        '''Do something when the scripted object is activated/clicked/etc.
        Script.tick() and Script.activate() are not usually called from
        the same instance.
        Do not rely on saved instance state. Store it in the database.
        '''
        pass

    def roll(self, dicestring):
        '''Roll dice specified by dicestring and return the value.
        Does not allow more dice than the MAX_DICE_AMOUNT setting
        to be rolled at once.'''

        rolls, num, sides, mod = parse(dicestring)
        num = int(num)
        sides = int(sides)
        mod = int(mod)
        if num > MAX_DICE_AMOUNT:
            raise UserWarning("Cannot roll more than %d dice at once." % MAX_DICE_AMOUNT)

        rolls = []
        for i in xrange(num):
            #print "Rolling dice #%d of %d: %f%% done." % (i, num, (float(i)/float(num))*100)
            rolls.append(random.randrange(1, int(sides)+1)+int(mod))
        return sum(rolls)

    def say(self, message):
        '''Write the given text to the zone message database.'''
        Message(sender=self.me_obj.name, body=message, loc=self.me_obj.loc, player_generated=False).save()
        print "[%s] %s: %s" % (datetime.datetime.now(), self.me_obj.name, message)

    def rand_say(self, sayings):
        '''Pick a random saying from sayings and say it.'''
        self.say(random.choice(sayings))

    def tick(self):
        pass

    def move(self, xmod, ymod, zmod):
        self.me_obj.loc['x'] += xmod
        self.me_obj.loc['y'] += ymod
        self.me_obj.loc['z'] += zmod
        self.me_obj.last_modified = datetime.datetime.now()

        from helpers import manhattan
        ourx, oury = self.me_obj.loc['x'], self.me_obj.loc['y']
        for o in Object.objects(physical=True):
            # Is the distance between that object and the character less than 3?
            if o.loc and manhattan(o.loc['x'], o.loc['y'], ourx, oury) < 1:
                # We collided against something, so return now and don't
                # save the location changes into the database.
                return False
        else:
            # We didn't collide with any objects.
            self.me_obj.save()
            return True

    def wander(self):
        return self.move(random.randint(-1, 1), random.randint(-1, 1), random.randint(-1, 1))


