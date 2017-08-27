# ##### BEGIN AGPL LICENSE BLOCK #####
# This file is part of SimpleMMO.
#
# Copyright (C) 2011, 2012  Charles Nelson
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ##### END AGPL LICENSE BLOCK #####

'''This module contains all the models for the SQL ~~Elixir~~ Peewee tables.'''

from peewee import *
from playhouse.sqlite_ext import SqliteExtDatabase, JSONField
from playhouse.shortcuts import model_to_dict, RetryOperationalError

import datetime

class RetryDB(RetryOperationalError, SqliteExtDatabase):
    pass

db = RetryDB(None, fields={'json':'json'})
# db = RetryDB(None, fields={'json':'json'}, pragmas=[('journal_mode', 'wal')])

# db = PooledSqliteExtDatabase(None, pragmas=[('journal_mode', 'wal')], max_connections=30, stale_timeout=3600, check_same_thread=False, fields={'json':'json'})

import json 
class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, complex):
            return [obj.real, obj.imag]

        if isinstance(obj, BaseModel):
            return model_to_dict(obj)

        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()

        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)

class BaseModel(Model):
    class Meta:
        database = db

    @classmethod
    def exists(cls, *args, **kwargs):
        return cls.select().where(*args, **kwargs).exists()

    def json_dumps(self):
        return json.dumps(model_to_dict(self), cls=ComplexEncoder)

class User(BaseModel):
    '''User contains details useful for authenticating a user for when they
    initially log in.'''

    username = CharField(unique=True)
    password = CharField()
    email = CharField(null=True)
    # Also has 'characters'

    def __repr__(self):
        uname = self.username
        s = "s"*(len(self.characters)-1)
        chars = ', '.join([c.name for c in self.characters])
        return '<User "%s" owning character%s: %s.>' % (uname, s, chars)

class Character(BaseModel):
    '''Character contains the details for characters that users may control.'''

    name = CharField(unique=True)

    speed = FloatField(default=1)

    user = ForeignKeyField(User, related_name='characters')
    # Also has 'zones'


    def __repr__(self):
        return '<Character "%s" owned by "%s">' % (self.name, self.user.username)

class Zone(BaseModel):
    '''Zone stores connection information about the zoneservers.'''

    zoneid = CharField(unique=True)
    port = IntegerField(unique=False)
    url = CharField(unique=True, null=True)

    character = ForeignKeyField(Character, related_name='zones')

class Message(BaseModel):
    '''A text message from a player, for cross-zone messaging.'''

    date_sent = DateTimeField(default=datetime.datetime.now)
    sender = CharField()
    recipient = CharField(null=True, default=u'')
    channel = IntegerField(null=True, default=0)
    body = CharField(null=True, default=u'')

class Object(BaseModel):
    '''In-world objects.'''

    name = CharField()
    resource = CharField(default="none")
    owner = CharField(null=True)

    loc_x = FloatField(default=0)
    loc_y = FloatField(default=0)
    loc_z = FloatField(default=0)

    rot_x = FloatField(default=0)
    rot_y = FloatField(default=0)
    rot_z = FloatField(default=0)

    scale_x = FloatField(default=1)
    scale_y = FloatField(default=1)
    scale_z = FloatField(default=1)

    speed = FloatField(default=1)
    vel_x = FloatField(default=0)
    vel_y = FloatField(default=0)
    vel_z = FloatField(default=0)

    states = JSONField(default=[])
    physical = BooleanField(default=True)
    last_modified = DateTimeField(default=datetime.datetime.now)

    scripts = JSONField(default=[])

    def set_modified(self, date_time=None):
        if date_time is None:
            date_time = datetime.datetime.now()
        self.last_modified = date_time
        self.save()

    @staticmethod
    def get_objects(since=None, physical=None, limit=None, player=None, scripted=None, name=None):
        # TODO: Needs integration test.
        obj = Object.select()

        if since is not None:
            obj = obj.where(Object.last_modified>=since)

        if physical is not None:
            obj = obj.where(Object.physical==physical)

        if player is not None:
            obj = obj.where(Object.states.contains('player')).where(Object.name==player)

        if scripted is not None:
            obj = obj.where(Object.scripts!=None) # TODO: Have this only return objects with scripts.

        if name is not None:
            obj = obj.where(Object.name==name)

        obj = obj.order_by(Object.last_modified.desc())

        if limit is not None:
            obj = obj.limit(limit)

        if limit == 1:
            return obj

        return [o for o in obj]

class Message(BaseModel):
    message = CharField()
    sender = CharField()
    loc_x = FloatField()
    loc_y = FloatField()
    loc_z = FloatField(default=0)
    player_generated = BooleanField()

class ScriptedObject(Object):
    pass

def setup(db_uri='simplemmo.sqlite', echo=False):
    print "dburi:", db_uri
    global db
    db.init(db_uri)
    db.connect()
    db.create_tables([User, Character, Zone, Message, Object], True)


if __name__ == "__main__":
    setup(db_uri=":memory:")

    u, _ = User.get_or_create(username="user", password="pass")
    Character.get_or_create(name="Groxnor")
    Character.get_or_create(name="Bleeblebox")

    print [_ for _ in User.select()]
    print [_ for _ in Character.select()]

    print u
    print "Characters for 'user':", [_ for _ in u.characters]
