
import datetime

import mongoengine as me

class IntVector(me.EmbeddedDocument):
    '''A document for holding documents with three integer vectors: 
        x, y and z.'''
    x = me.IntField(default=0)
    y = me.IntField(default=0)
    z = me.IntField(default=0)

class FloatVector(me.EmbeddedDocument):
    '''A document for holding documents with three float vectors:
        x, y and z.'''
    x = me.FloatField(default=0)
    y = me.FloatField(default=0)
    z = me.FloatField(default=0)

class Object(me.Document):
    '''In-world objects.'''
    name = me.StringField(default="")
    resource = me.StringField(default="")

    loc = me.EmbeddedDocumentField(IntVector) # FIXME: Make this a floatvector.
    rot = me.EmbeddedDocumentField(FloatVector)
    scale = me.EmbeddedDocumentField(FloatVector)
    vel = me.EmbeddedDocumentField(FloatVector)

    states = me.ListField(me.StringField())
    physical = me.BooleanField(default=True)
    last_modified = me.DateTimeField(default=datetime.datetime.now)

    meta = {'indexes': ['last_modified',
                        'loc.x', 'loc.y', 'loc.z',
                        'states',
                        'physical',
                        ]}

    def set_modified(self, date_time=None):
        if date_time is None:
            date_time = datetime.datetime.now()
        self.last_modified = date_time
        self.save()

class ScriptedObject(Object):
    scripts = me.ListField(me.StringField())

class Character(ScriptedObject):
    '''Players' characters.'''
    speed = me.FloatField(default=5)

class Message(me.Document):
    '''A message said and displayed as if it were in world.
    Used only for zone-local messages.'''
    sent = me.DateTimeField(default=datetime.datetime.now)
    sender = me.StringField(default="")
    body = me.StringField(default="")
    loc = me.EmbeddedDocumentField(IntVector)
    player_generated = me.BooleanField(default=False)

    meta = {'indexes': ['sent', 'loc'],
            'allow_inheritance': True,
            }

class PrivateMessage(Message):
    '''A message from and to a specific thing.'''
    recipient = me.StringField(default="")
    meta = {'indexes': ['recipient'],
            'allow_inheritance': True,
            }

