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

'''This module contains all the models for the SQL Elixir tables.'''

from elixir import Entity, Field
from elixir import OneToMany, ManyToOne
from elixir import UnicodeText, Integer, DateTime
from elixir import using_options
from elixir import metadata, setup_all, create_all
from elixir import session

import datetime

metadata.bind = "sqlite:///simplemmo.sqlite"
metadata.bind.echo = True

class User(Entity):
    '''User contains details useful for authenticating a user for when they
    initially log in.'''

    using_options(tablename="user")

    username = Field(UnicodeText, unique=True, required=True)
    password = Field(UnicodeText, required=True)
    characters = OneToMany('Character') # A User has Many Characters

    def __repr__(self):
        uname = self.username
        s = "s"*(len(self.characters)-1)
        chars = ', '.join([c.name for c in self.characters])
        return '<User "%s" owning character%s: %s.>' % (uname, s, chars)

class Character(Entity):
    '''Character contains the details for characters that users may control.'''

    using_options(tablename="character")

    name = Field(UnicodeText, unique=True, required=True)
    user = ManyToOne('User', required=True)
    zones = OneToMany('Zone')

    def __repr__(self):
        return '<Character "%s" owned by "%s">' % (self.name, self.user.username)

class Zone(Entity):
    '''Zone stores connection information about the zoneservers.'''
    using_options(tablename="zone")

    zoneid = Field(UnicodeText, unique=True, primary_key=True)
    port = Field(Integer, unique=True)
    character = ManyToOne('Character')

class Message(Entity):
    '''A text message from a player, for cross-zone messaging.'''
    using_options(tablename="message")

    date_sent = Field(DateTime, default=datetime.datetime.now)
    sender = Field(UnicodeText, required=True)
    recipient = Field(UnicodeText)
    channel = Field(Integer, unique=True)
    body = Field(UnicodeText, default='')


setup_all()
create_all()

if __name__ == "__main__":

    u = User(username="user", password="pass")
    Character(name="Groxnor", user=u)
    Character(name="Bleeblebox", user=u)
    session.commit()

    print User.query.all()
    print Character.query.all()

    print "Characters for 'user':", Character.get_by(user=u)
