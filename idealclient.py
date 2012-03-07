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

'''This is an example implementation of an ideal client.
It is exceptionally stupid and fragile.
It should only be used as an example of how to make calls to the servers.'''

import exceptions
from time import sleep
import json
import pdb
import datetime

import requests

from settings import *
from settings import DEFAULT_USERNAME, DEFAULT_PASSWORD

# Some settings:
USERNAME = DEFAULT_USERNAME
ADMINUSERNAME = "admin"
PASSWORD = DEFAULT_PASSWORD
DEBUG = True

# What hostname are the servers on
PREFIX = "http://" # FIXME: Use proper name.
HOSTNAME = "localhost"

# Server URLs
AUTHSERVER = "%s%s:%d" % (PREFIX, HOSTNAME, AUTHSERVERPORT)
CHARSERVER = "%s%s:%d" % (PREFIX, HOSTNAME, CHARSERVERPORT)
ZONESERVER = "%s%s:%d" % (PREFIX, HOSTNAME, MASTERZONESERVERPORT)

# A global holder for our cookies.
COOKIES = {}

# A global for storing the current zone URL we're in.
CURRENTZONE = ""

# A global for storing the current character.
CURRENTCHAR = ""

# A global websocket connection for movement updates
MOVEMENTWEBSOCKET = None

# When was our last object update fetched.
LASTOBJUPDATE = None

class ConnectionError(exceptions.Exception):
    def __init__(self, param):
        self.param = param
        return
    def __str__(self):
        return repr(self.param)

def retry(func, *args, **kwargs):
    sleeptime = 2
    server_exists = False
    while not server_exists:
        try:
            server_exists = func(*args, **kwargs)
            if server_exists:
                break # If we connect succesfully, break out of the while
        except Exception, exc:
            # Exceptions mean we failed to connect, so retry.
            if DEBUG:
                print "Connecting failed:", exc

        print "Reconnecting in %.01f seconds..." % sleeptime
        sleep(sleeptime)
        sleeptime = sleeptime**1.5
        if sleeptime > CLIENT_TIMEOUT:
            raise requests.exceptions.Timeout("Gave up after %d seconds." % int(CLIENT_TIMEOUT))
    return True

class InvalidResponse(Exception):
    def __init__(self, status_code, content):
        self.status_code = status_code
        self.content = content

    def __str__(self):
        return "%d: %s" % (self.status_code, self.content)

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

# Ping main server to make sure it's up, and really an authserver
def ping_authserver():
    r = requests.get(''.join((AUTHSERVER, "/ping")))
    content = r.content

    if content != "pong":
        raise ConnectionError("Something went wrong." % content)
    else:
        return True

# Send username/password credentials to server
# Server sends back a cookie that we send with all our requests.
def login(username, password):
    data = {"username": username, "password": password}
    r = requests.post(''.join((AUTHSERVER, "/login")), data=data, cookies=COOKIES)
    content = json_or_exception(r)
    COOKIES.update(r.cookies)
    return content

# Ask authserver for list of characters associated with this account
# authserver returns a list of characters
def get_characters():
    r = requests.get(''.join((AUTHSERVER, "/characters")), cookies=COOKIES)
    content = json_or_exception(r)
    return content

# We could also query any details about the character like inventory 
#   or money or current stats at this point

# We pick a character we want to play and query the charserver for its current zone
# charserver returns the zone id, which uniquely identifies it persistently.
def get_zone(charname=None):
    if charname is None:
        charname = CURRENTCHAR

    r = requests.get(''.join((CHARSERVER, '/', charname, '/zone')), )
    content = json_or_exception(r)
    return content['zone']

# We then send a request to the master zone server for the url to the given zone
# If it's online already, send us the URL
# If it's not online, spin one up and send it when ready.
def get_zoneserver(zone):
    r = requests.get(''.join((ZONESERVER, '/', zone)), cookies=COOKIES)
    print r.status_code, r.content
    content = json_or_exception(r)
    return content

# Request all objects in the zone. (Terrain, props, players are all objects)
# Bulk of loading screen goes here while we download object info.
def get_all_objects(zone=None):
    if zone is None:
        zone = CURRENTZONE
        print zone
    r = requests.get(''.join((zone, '/objects')), cookies=COOKIES)
    content = json_or_exception(r)
    return content

def get_objects_since(since, zone=None):
    if zone is None:
        zone = CURRENTZONE
    data = {"since": since.strftime(DATETIME_FORMAT)}
    r = requests.get(''.join((zone, '/objects')), cookies=COOKIES, params=data)
    content = json_or_exception(r)
    return content

# We send a request to the zoneserver to mark our character as online/active
def set_status(zone=None, character=None, status='online'):
    if zone is None:
        zone = CURRENTZONE
    if character is None:
        character = CURRENTCHAR

    data = {'character': character, 'status': status}
    r = requests.post(''.join((zone, '/setstatus')), cookies=COOKIES, data=data)
    content = json_or_exception(r)
    return content

# Send an initial movement message to the zoneserver's movement handler to open the connection
def send_movement_ws(zone, character, xmod=0, ymod=0):
    import websocket
    global MOVEMENTWEBSOCKET
    if MOVEMENTWEBSOCKET is None:
        connstr = zone.replace("http://", "ws://")
        connstr = ''.join((connstr, "/movement"))
        websocket.enableTrace(True)
        print connstr
        print websocket.create_connection(connstr)
        MOVEMENTWEBSOCKET = create_connection(connstr)
    else:
        print "Using old websocket connection."

    MOVEMENTWEBSOCKET.send(json.dumps({'command': 'mov', 'char':character, 'x':xmod, 'y':ymod}))
    return json.loads(ws.recv())

def send_movement(zone=None, character=None, xmod=0, ymod=0, zmod=0):
    if xmod is 0 and ymod is 0 and zmod is 0:
        # No-op.
        return

    if zone is None:
        zone = CURRENTZONE
    if character is None:
        character = CURRENTCHAR

    data = {'character': character, 'x': xmod, 'y': ymod, 'z': zmod}
    r = requests.post(''.join((zone, '/movement')), cookies=COOKIES, data=data)
    content = json_or_exception(r)
    return content

### Repetitive ###
# Every second or so, request objects that have changed or been added since the last request.
# Send movement keys to the movement handler of the zoneserver as fast as possible to move the character about

if __name__ == "__main__":

    # Try to ping the authserver
    # If connecting fails, wait longer each time
    retry(ping_authserver)

    # Since the server is up, authenticate.
    if login(USERNAME, PASSWORD) is True:
        print "authenticated"

    chars = get_characters()
    print "Got %r as characters." % chars

    global CURRENTCHAR
    CURRENTCHAR = chars[0]
    import random
#     CURRENTCHAR = ''.join([random.choice(list("qwertyuiopasdfghjklzxcvbnm")) for c in range(10)]).title()

    zone = get_zone()
    print "Got %r as zone." % zone

    zoneserver = get_zoneserver(zone)
    print "Got %s as zone url." % zoneserver

    global CURRENTZONE
    CURRENTZONE = zoneserver

    objects = get_all_objects()
    import pprint
    print pprint.pprint(objects)
    print "Got %d objects from the server." % len(objects)
    LASTOBJUPDATE = datetime.datetime.now()

    if set_status():
        print "Set status in the zone to online."

    movresult = send_movement(xmod=0, ymod=0, zmod=1)
    if movresult:
        print "Sent our first movement packet to make sure we show up."

    newobjs = get_objects_since(LASTOBJUPDATE)
    print "Got %d new objects since our last full update." % len(newobjs)

    from random import randint
    import time
    while True:
        movresult = send_movement(xmod=randint(-1, 1), ymod=randint(-1, 1))

        time.sleep(.5)
