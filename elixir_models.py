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
from playhouse.sqlite_ext import SqliteExtDatabase

import datetime

db = SqliteExtDatabase('sqlite:///simplemmo.db', fields={'json':'json'})

class BaseModel(Model):
    class Meta:
        database = db

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

    user = ForeignKeyField(User, related_name='characters')
    # Also has 'zones'


    def __repr__(self):
        return '<Character "%s" owned by "%s">' % (self.name, self.user.username)

class Zone(BaseModel):
    '''Zone stores connection information about the zoneservers.'''

    zoneid = CharField(unique=True)
    port = IntegerField(unique=True)
    url = CharField(unique=True, null=True)

    character = ForeignKeyField(Character, related_name='zones')

class Message(BaseModel):
    '''A text message from a player, for cross-zone messaging.'''

    date_sent = DateTimeField(default=datetime.datetime.now)
    sender = CharField()
    recipient = CharField(null=True, default=u'')
    channel = IntegerField(null=True, default=0)
    body = CharField(null=True, default=u'')

def setup(db_uri='sqlite:///simplemmo.sqlite', echo=False):
    print "dburi:", db_uri
    global db
    db = SqliteExtDatabase(db_uri, fields={'json':'json'})
    db.connect()
    db.create_tables([User, Character, Zone, Message], True)


if __name__ == "__main__":
    setup(db_uri=":memory:")

    u, _ = User.get_or_create(username="user", password="pass")
    Character.get_or_create(name="Groxnor")
    Character.get_or_create(name="Bleeblebox")

    print [_ for _ in User.select()]
    print [_ for _ in Character.select()]

    print u
    print "Characters for 'user':", [_ for _ in u.characters]
