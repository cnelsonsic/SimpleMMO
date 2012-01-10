# -*- coding: utf-8 -*-
'''This is an example implementation of an ideal client.
It is exceptionally stupid and fragile.
It should only be used as an example of how to make calls to the servers.'''

import exceptions
from time import sleep
import json
import pdb

import requests

from settings import *

# Some settings:
USERNAME = "user"
PASSWORD = "pass"
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

class ConnectionError(exceptions.Exception):
    def __init__(self, param):
        self.param = param
        return
    def __str__(self):
        return repr(self.param)

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
    content = r.content

    COOKIES.update(r.cookies)

    if r.status_code == 200:
        return True
    else:
        return r

# Ask authserver for list of characters associated with this account
# authserver returns a list of characters
def get_characters():
    r = requests.get(''.join((AUTHSERVER, "/characters")), cookies=COOKIES)
    if r.status_code == 200:
        return json.loads(r.content)
    else:
        return r

# We could also query any details about the character like inventory 
#   or money or current stats at this point

# We pick a character we want to play and query the charserver for its current zone
# charserver returns the zone id, which uniquely identifies it persistently.
def get_zone(charname=None):
    if charname is None:
        charname = CURRENTCHAR

    r = requests.get(''.join((CHARSERVER, '/', charname, '/zone')), )
    if r.status_code == 200:
        return json.loads(r.content).get('zone')
    else:
        return r

# We then send a request to the master zone server for the url to the given zone
# If it's online already, send us the URL
# If it's not online, spin one up and send it when ready.
def get_zoneserver(zone):
    r = requests.get(''.join((ZONESERVER, '/', zone)), cookies=COOKIES)
    if r.status_code == 200:
        return r.content
    else:
        return r

# Request all objects in the zone. (Terrain, props, players are all objects)
# Bulk of loading screen goes here while we download object info.
def get_all_objects(zone=None):
    if zone is None:
        zone = CURRENTZONE
    r = requests.get(''.join((zone, '/objects')), cookies=COOKIES)
    if r.status_code == 200:
        return json.loads(r.content)
    else:
        return r

# We send a request to the zoneserver to mark our character as online/active
def set_status(zone=None, character=None, status='online'):
    if zone is None:
        zone = CURRENTZONE
    if character is None:
        character = CURRENTCHAR

    data = {'character': character, 'status': status}
    r = requests.post(''.join((zone, '/setstatus')), cookies=COOKIES, data=data)
    if r.status_code == 200:
        return True
    else:
        return r

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
    if zone is None:
        zone = CURRENTZONE
    if character is None:
        character = CURRENTCHAR

    data = {'character': character, 'xmod': xmod, 'ymod': ymod, 'zmod': zmod}
    r = requests.post(''.join((zone, '/movement')), cookies=COOKIES)
    if r.status_code == 200:
        return True
    else:
        return r

### Repetitive ###
# Every second or so, request objects that have changed or been added since the last request.
# Send movement keys to the movement handler of the zoneserver as fast as possible to move the character about

if __name__ == "__main__":

    # Try to ping the authserver
    # If connecting fails, wait longer each time
    sleeptime = 2
    authserver_exists = False
    while not authserver_exists:
        try:
            authserver_exists = ping_authserver()
            if authserver_exists:
                break # If we connect succesfully, break out of the while
        except Exception, exc:
            # ConnectionErrors mean we failed to connect, so retry.
            if DEBUG:
                print "Connecting failed:", exc

        print "Reconnecting in %.01f seconds..." % sleeptime
        sleep(sleeptime)
        sleeptime = sleeptime**1.5

    # Since the server is up, authenticate.
    if login(USERNAME, PASSWORD) is True:
        print "authenticated"

    chars = get_characters()
    print "Got %r as characters." % chars

    global CURRENTCHAR
    CURRENTCHAR = chars[0]

    zone = get_zone()
    print "Got %r as zone." % zone

    zoneserver = get_zoneserver(zone)
    print "Got %s as zone url." % zoneserver

    global CURRENTZONE
    CURRENTZONE = zoneserver

    objects = get_all_objects()
    print "Got %d objects from the server." % len(objects)

    if set_status():
        print "Set status in the zone to online."

    movresult = send_movement(xmod=0, ymod=0)
    if movresult:
        print "Sent our first movement packet to make sure we show up."

