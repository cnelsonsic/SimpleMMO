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
import logging
logging.getLogger('requests.packages.urllib3.connectionpool').setLevel(logging.ERROR)

import settings


class ClientError(Exception):
    pass


class RegistrationError(ClientError):
    pass


class AuthenticationError(ClientError):
    pass


class ConnectionError(ClientError):
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
        self.init_logging()

        self.characters = {}
        self.last_character = None

        self.last_zone = None
        self.zones = {}

        self.last_object_update = datetime.datetime(2010, 1, 1)
        self.objects = {}

        self.last_message_update = datetime.datetime(2010, 1, 1)
        self.messages = {}

        self.last_user = None
        self.cookies = {}
        if username and password:
            if not self.authenticate(username=username, password=password):
                raise AuthenticationError("Authentication failed with credentials: '%s':'%s'" % (username, password))

    def init_logging(self):
        self.logger = logging.getLogger('clientlib')

    def log(self, level, message, *args, **kwargs):
        self.logger.log(level, message, *args, **kwargs)

    def info(self, message):
        self.log(logging.INFO, message)

    def error(self, message):
        self.log(logging.ERROR, message)

    def post(self, *args, **kwargs):
        url = ''.join(args)
        try:
            r = requests.post(url, **kwargs)
        except requests.ConnectionError:
            self.error("Host {0} is unreachable."
                       .format(url))
            raise ConnectionError
        self.info("POST: %s (%r)" % (url, kwargs))
        return r

    def get(self, *args, **kwargs):
        url = ''.join(args)
        try:
            r = requests.get(url, **kwargs)
        except requests.ConnectionError:
            self.error("Host {0} is unreachable."
                       .format(url))
            raise ConnectionError
        self.info("GET: %s (%r)" % (url, kwargs))
        return r

    def ping(self):
        try:
            r = self.get(settings.AUTHSERVER, '/ping')
        except ConnectionError:
            return False

        if r.content == 'pong':
            return True
        else:
            return False

    def register(self, username, password, email=None):
        if username == self.last_user:
            return 'Registration successful.'

        data = {"username": username, "password": password, "email": email}
        r = self.post(settings.AUTHSERVER, "/register", data=data)

        if r.status_code == 200:
            self.last_user = username
            return str(r.content)
        else:
            raise RegistrationError(r.content)

    def authenticate(self, username, password):
        data = {"username": username, "password": password}
        r = self.post(settings.AUTHSERVER, "/login", data=data)

        if r.status_code == 200:
            self.last_user = username
            self.cookies.update({'user': r.cookies.get('user')})
            self._populate_characters()
            return True
        elif r.status_code == 401:
            self.cookies = {}
            return False
        else:
            print r

    def create_character(self, character_name):
        '''Create a character. Think of this as making a "new file".
        Character data (statistic points, race, class, etc) is set later.
        '''
        data = {'character_name': character_name}
        r = self.post(settings.CHARSERVER, "/new", cookies=self.cookies, data=data)

        if r.status_code == 400 or not r.content:
            raise ClientError("Creating character %s failed: %s" % (character_name, r.content))
        elif r.status_code != 200:
            raise UnexpectedHTTPStatus("CharServer", r.status_code, r.content)

        self.info("Creating a character named %s" % r.content)
        self._populate_characters()
        return r.content


    def _populate_characters(self):
        '''Get the characters for the currently logged in.'''
        r = self.get(settings.AUTHSERVER, "/characters", cookies=self.cookies)

        if r.status_code == 200:
            content = json.loads(r.content)
            if not content:
                # When authenticating for the first time there will be no characters.
                return

            for charname in content:
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

        url = ''.join((settings.CHARSERVER, "/%s/zone" % char.name))
        r = self.get(url, cookies=self.cookies)
        if r.status_code == 200:
            data = json.loads(r.content)
            zone = data.get('zone')
            char.zone = zone
            self.characters[char.name].zone = zone
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

        r = self.get(settings.ZONESERVER, "/%s" % zoneid, cookies=self.cookies)

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
            zone = self.zones.get(zone)


        data = {"since": self.last_object_update.strftime(settings.DATETIME_FORMAT)}
        r = self.get(zone, '/objects', cookies=self.cookies, params=data)

        if r.status_code == 200:
            objects = json.loads(r.content)
            self.info("Got %d objects."%len(objects))
            for obj in objects:
                self.objects[obj['id']] = obj
        else:
            raise UnexpectedHTTPStatus("ZoneServer %s" % zone, r.status_code, r.content)

        self.last_object_update = datetime.datetime.now()
        return objects

    def get_messages(self, zone=None):
        '''Get messages from the zone only.
        In the future, get game-wide messages.'''
        if zone is None:
            zone = self.get_zone_url()

        if "http://" not in zone:
            # zone is probably a zoneid
            zone = self.zones.get(zone)

        data = {"since": self.last_message_update.strftime(settings.DATETIME_FORMAT)}
        r = self.get(zone, '/messages', cookies=self.cookies, params=data)

        if r.status_code == 200:
            messages = json.loads(r.content)
            for msg in messages:
                msgid = msg.get('_id', {}).get('$oid')
                self.messages[msgid] = msg
        else:
            raise UnexpectedHTTPStatus("ZoneServer %s" % zone, r.status_code, r.content)

        self.last_message_update = datetime.datetime.now()
        return messages

    def set_character_status(self, character, status='online'):
        char = self.get_char_obj(character_name=character)

        if not char.zone:
            self.get_zone(character)

        if char.online != status:
            data = {'character': char.name, 'status': status}
            r = self.post(self.get_zone_url(char.zone), '/setstatus', cookies=self.cookies, data=data)
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
        r = self.post(self.get_zone_url(char.zone), '/movement', cookies=self.cookies, data=data)
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
        self.last_character = character

    def activate(self, object_id, character=None):
        '''Activate (click) an object by its id.'''
        char = self.get_char_obj(character)
        data = {'character': char.name}
        r = self.post(self.get_zone_url(char.zone), '/activate/%s' % object_id, cookies=self.cookies, data=data)
        content = json_or_exception(r)
        if content:
            return True
        else:
            raise ClientError("Could not activate object %s. Content was: %s" % (object_id, content))


def main(ticks=10):
    c = Client()

    # Authenticate.
    username = "Kilrox"
    password = "kilroxrox"
    if c.register(username, password):
        print "registered"

    if c.authenticate(username, password) is True:
        print "authenticated"

    print"Created a character named %s" % c.create_character("Kilroxor")

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
