# -*- coding: utf-8 -*-
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

'''This is a client for SimpleMMO.
It should be fairly resilient to inevitable bad/unexpected responses
from the server, and is generally how clients should connect.

Authentication is automatic when you instantiate the client.
>>> c = Client(username="Username", password="password")

Though, you can call it without those kwargs, and authenticate separately:
>>> c = Client()
>>> c.authenticate(username="Username", password="password")

We need to know which characters our user has:
>>> c.characters
['Groxnor', 'Rumtiddlykins']

We'll need to know what zone id the character is in:
>>> c.get_zone('Groxnor')
playerinstance-GhibliHills-Groxnor

To connect, we need to get the zone URL:
>>> c.get_zone_url('playerinstance-GhibliHills-Groxnor')
http://127.0.0.1:1234

Now we need all the objects from the zoneserver
>>> c.objects['http://127.0.0.1:1234']
[]
>>> c.objects['playerinstance-GhibliHills-Groxnor']
[]

Now that we have the objects loaded from the network, we
can mark our character as online
>>> c.characters('Groxnor').online = True

And send a no-op movement message so we show up.
>>> c.characters('Groxnor').move()
True

'''

import datetime
import json
import requests

import settings


class ClientError(Exception):
    pass


class AuthenticationError(ClientError):
    pass


class UnexpectedHTTPStatus(ClientError):
    def __init__(self, message, status_code, content):
        self.message = message
        self.status_code = status_code
        self.content = content

    def __str__(self):
        return "%s (%d: %s)" % (self.message, self.status_code, self.content)


def json_or_exception(response, message='Got an unexpected response.'):
    '''Convert an HTTPResponse to JSON, if its status is 200 OK.
    Otherwise, raise an exception.'''
    if response.status_code == 200:
        try:
            return json.loads(response.content)
        except ValueError:
            return response.content
    else:
        raise UnexpectedHTTPStatus(message, response.status_code, response.content)


class Character(object):
    _online_states = {'online': True, 'offline': False}

    def __init__(self, name):
        self.name = name
        self.zone = None

        self._online = False

    def __repr__(self):
        return "Character(name=%r)" % (self.name,)

    @property
    def online(self):
        return self._online

    @online.setter
    def online(self, value):
        if value != self.online:
            self._online = self._online_states.get(value, False)
        return self._online


class Client(object):
    def __init__(self, username=None, password=None):
        self.characters = {}
        self.last_character = None

        self.zones = {}

        self.last_object_update = datetime.datetime(2010, 1, 1)
        self.objects = {}

        self.cookies = {}
        if username and password:
            if not self.authenticate(username=username, password=password):
                raise AuthenticationError("Authentication failed with credentials: '%s':'%s'" % (username, password))

    def authenticate(self, username, password):
        data = {"username": username, "password": password}
        r = requests.post(''.join((settings.AUTHSERVER, "/login")), data=data)
        if r.status_code == 200:
            self.cookies.update(r.cookies)
            self._populate_characters()
            return True
        elif r.status_code == 401:
            self.cookies = {}
            return False

    def _populate_characters(self):
        '''Get the characters for the currently logged in.'''
        r = requests.get(''.join((settings.AUTHSERVER, "/characters")), cookies=self.cookies)
        if r.status_code == 200:
            for charname in json.loads(r.content):
                self.characters[charname] = Character(charname)
                self.last_character = charname

    def get_zone(self, character=None):
        char = self.get_char_obj(character_name=character)

        # Try to just return the cached zone
        try:
            zone = char.zone
            if zone:
                return zone
        except (AttributeError, KeyError):
            # Cache miss. :(
            pass

        r = requests.get(''.join((settings.CHARSERVER, "/%s/zone" % character)), cookies=self.cookies)
        if r.status_code == 200:
            data = json.loads(r.content)
            zone = data.get('zone')
            self.characters[character].zone = zone
            return zone

    def get_zone_url(self, zoneid=None):
        '''Get the zone server URI for a given zoneid.'''
        if zoneid is None:
            # No zoneid specified, just grab the first character's zone.
            if self.characters.keys():
                zoneid = self.get_zone()
            else:
                raise ClientError("A zoneid is required if there are no characters.")

        # Try to just return the cached zone_url
        try:
            return self.zones[zoneid]
        except KeyError:
            # Cache miss :(
            pass

        r = requests.get(''.join((settings.ZONESERVER, "/%s" % zoneid)), cookies=self.cookies)
        if r.status_code == 200:
            zoneurl = r.content
            if zoneurl == "":
                raise ClientError("Did not get a zone URL for zoneid %s." % zoneid)
            else:
                zone = r.content
                self.zones[zoneid] = zone
                self.last_zone = zone
                return zone
        else:
            raise UnexpectedHTTPStatus("MasterZoneServer", r.status_code, r.content)

    def get_objects(self, zone=None):
        if zone is None:
            zone = self.get_zone_url()

        if "http://" not in zone:
            # zone is probably a zoneid
            zone = self.zone(zone)

        data = {"since": self.last_object_update.strftime(settings.DATETIME_FORMAT)}
        r = requests.get(''.join((zone, '/objects')), cookies=self.cookies, params=data)

        if r.status_code == 200:
            objects = json.loads(r.content)
            for obj in objects:
                objid = obj.get('_id', {}).get('$oid')
                self.objects[objid] = obj
        else:
            raise UnexpectedHTTPStatus("ZoneServer %s" % zone, r.status_code, r.content)

        self.last_object_update = datetime.datetime.now()
        return objects

    def set_character_status(self, character, status='online'):
        char = self.get_char_obj(character_name=character)

        if not char.zone:
            raise ClientError("Unknown zone value for character. Call get_zone first.")

        if char.online != status:
            data = {'character': char.name, 'status': status}
            r = requests.post(''.join((self.get_zone_url(char.zone), '/setstatus')), cookies=self.cookies, data=data)
            result = json_or_exception(r)
            if result is True:
                char.online = status
                return True
            elif result is False:
                raise ClientError('Setting status %s failed.' % status)
        else:
            # No need to update the character's status.
            return True

    def move_character(self, character=None, xmod=0, ymod=0, zmod=0):
        char = self.get_char_obj(character_name=character)

        if char.online != True:
            raise ClientError("Cannot move character, not online: %s" % char.online)

        data = {'character': char.name, 'x': xmod, 'y': ymod, 'z': zmod}
        r = requests.post(''.join((self.get_zone_url(char.zone), '/movement')), cookies=self.cookies, data=data)
        content = json_or_exception(r)
        if content is True:
            return True
        else:
            # Could not move. Probably due to collision.
            return content

    def get_char_obj(self, character_name):
        if not character_name:
            # No character passed, grab the first one.
            character_name = self.last_character

        try:
            char = self.characters[character_name]
        except KeyError:
            raise ClientError("Could not find Character object in Client.")

        return char

    def set_online(self, character):
        self.set_character_status(character, 'online')
        self.move_character(character)


def main(ticks=10):
    c = Client()

    # Authenticate.
    from settings import DEFAULT_USERNAME, DEFAULT_PASSWORD
    if c.authenticate(DEFAULT_USERNAME, DEFAULT_PASSWORD) is True:
        print "authenticated"

    # Freakin' automatic.
    print "Got %s as characters." % c.characters

    character = c.characters.keys()[0]
    zone = c.get_zone(character)
    print "Got %r as zone." % zone

    zoneserver = c.get_zone_url(zone)
    print "Got %s as zone url." % zoneserver

    objects = c.get_objects()
    import pprint
    print pprint.pprint(objects)
    print "Got %d objects from the server." % len(objects)

    if c.set_character_status(character, 'online'):
        print "Set status in the zone to online."

    c.move_character(character)
    print "Sent our first movement packet to make sure we show up."

    from random import randint
    import time
    total_ticks = 0
    while total_ticks < ticks:
        print "Tick"
        c.move_character(character, xmod=randint(-1, 1), ymod=randint(-1, 1))
        newobjs = c.get_objects()
        print "Got %d new objects since our last update." % len(newobjs)
        total_ticks += 1
        time.sleep(.5)
    return True

if __name__ == "__main__":
    main()
