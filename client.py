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


class InvalidResponse(Exception):
    def __init__(self, status_code, content):
        self.status_code = status_code
        self.content = content

    def __str__(self):
        return "%d: %s" % (self.status_code, self.content)

class ClientError(Exception):
    pass

class AuthenticationError(ClientError):
    pass

def json_or_exception(response):
    '''Convert an HTTPResponse to JSON, if its status is 200 OK.
    Otherwise, raise an exception.'''
    if response.status_code == 200:
        try:
            return json.loads(response.content)
        except ValueError:
            return response.content
    else:
        raise InvalidResponse(response.status_code, response.content)


class Character(object):
    def __init__(self, name):
        self.name = name
        self.zone = None

    def __repr__(self):
        return "Character(name=%r)" % (self.name,)


class Client(object):
    def __init__(self, username=None, password=None):
        self.characters = {}
        self.last_object_update = datetime.datetime(2010, 1, 1)
        self.objects = {}

        self.cookies = {}
        if username and password:
            if not self.authenticate(username=username, password=password):
                raise AuthenticationError("Authentication failed with credentials: '%s':'%s'" % (username, password))
            else:
                self._populate_characters()

    def authenticate(self, username, password):
        data = {"username": username, "password": password}
        r = requests.post(''.join((settings.AUTHSERVER, "/login")), data=data)
        if r.status_code == 200:
            self.cookies.update(r.cookies)
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

    def get_zone(self, character=None):
        if not character:
            # No character passed, grab the first one.
            character = self.characters.keys()[0]

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

        r = requests.get(''.join((settings.ZONESERVER, "/%s" % zoneid)), cookies=self.cookies)
        if r.status_code == 200:
            zoneurl = r.content
            if zoneurl == "":
                raise ClientError("Did not get a zone URL for zoneid %s." % zoneid)
            else:
                self.last_zone = r.content
                return self.last_zone
        else:
            raise ClientError("Unexpected status from MasterZoneServer: %d (%s)" % (r.status_code, r.content))

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
            raise ClientError("Unexpected status from ZoneServer %s: %d (%s)" % (zone, r.status_code, r.content))

        self.last_object_update = datetime.datetime.now()
        return objects

