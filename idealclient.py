'''This is an example implementation of an ideal client.
It won't work and probably won't even execute.'''

import exceptions
from time import sleep
import json

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
def authenticate(username, password):
    r = requests.get(''.join((AUTHSERVER, "/authenticate")), auth=(username, password))
    content = r.content

    if r.status_code == 200:
        return True
    else:
        return r

# Ask authserver for list of characters associated with this account
# authserver returns a list of characters
def get_characters(username, password):
    r = requests.get(''.join((AUTHSERVER, "/characters")), auth=(username, password))
    if r.status_code == 200:
        return json.loads(r.content)
    else:
        return r

# We could also query any details about the character like inventory 
#   or money or current stats at this point

# We pick a character we want to play and query the charserver for its current zone
# charserver returns the zone id, which uniquely identifies it persistently.
def get_zone(charname):
    r = requests.get(''.join((CHARSERVER, '/', charname, '/zone')), )
    if r.status_code == 200:
        return json.loads(r.content).get('zone')
    else:
        return r

# We then send a request to the master zone server for the url to the given zone
# If it's online already, send us the URL
# If it's not online, spin one up and send it when ready.
def get_zoneserver(username, password, zone):
    r = requests.get(''.join((ZONESERVER, '/', zone)), auth=(username, password))
    if r.status_code == 200:
        return r.content
    else:
        return r

# Request all objects in the zone. (Terrain, props, players are all objects)
# Bulk of loading screen goes here while we download object info.
def get_all_objects(zone, username, password):
    r = requests.get(''.join((zone, '/objects')), auth=(username, password))
    if r.status_code == 200:
        return json.loads(r.content)
    else:
        return r

# We send a request to the zoneserver to mark our character as online/active
def set_status(zone, username, password, character, status='online'):
    data = {'character': character, 'status': status}
    r = requests.post(''.join((zone, '/setstatus')), auth=(username, password))

# Send an initial movement message to the zoneserver's movement handler to open the connection

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
    if authenticate(USERNAME, PASSWORD) is True:
        print "authenticated"

    chars = get_characters(USERNAME, PASSWORD)
    print "Got %r as characters." % chars

    zone = get_zone(chars[0])
    print "Got %r as zone." % zone

    zoneserver = get_zoneserver(USERNAME, PASSWORD, zone)
    print "Got %s as zone url." % zoneserver
