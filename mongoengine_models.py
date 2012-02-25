
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

    loc = me.EmbeddedDocumentField(IntVector)
    rot = me.EmbeddedDocumentField(FloatVector)
    scale = me.EmbeddedDocumentField(FloatVector)
    vel = me.EmbeddedDocumentField(FloatVector)

    states = me.ListField(me.StringField())
    active = me.BooleanField(default=True)
    last_modified = me.DateTimeField(default=datetime.datetime.now)


    meta = {'indexes': ['last_modified',
                        'loc.x', 'loc.y', 'loc.z',
                        'states',
                        'active']}

class ScriptedObject(Object):
    scripts = me.ListField(me.StringField())

class Character(ScriptedObject):
    '''Players' characters.'''
    speed = me.FloatField(default=5)
