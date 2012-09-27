#!/usr/bin/env python2.7
'''Test the full client access sequence.
It is pretty much the anti-pattern of testing.
'''
import unittest

from tornado.web import Application
from tornado.testing import AsyncHTTPTestCase

import sys
sys.path.append(".")

import json
from urllib import urlencode

from authserver import PingHandler, AuthHandler, LogoutHandler, CharacterHandler
from charserver import CharacterZoneHandler
from zoneserver import ObjectsHandler, CharStatusHandler, MovementHandler

import settings

from elixir import session
from elixir_models import metadata, setup_all, create_all
from elixir_models import User

def set_up_db():
    '''Connects to an in-memory SQLite database,
    with the purpose of emptying it and recreating it.'''
    metadata.bind = "sqlite:///:memory:"
#     metadata.bind.echo = True
    setup_all()
    create_all()

# Call it the first time for tests that don't care if they have clean data.
set_up_db()

class TestFullIntegration(AsyncHTTPTestCase):
    def get_app(self):
        handlers = []
        handlers.append((r"/ping", PingHandler))
        handlers.append((r"/login", AuthHandler))
        handlers.append((r"/logout", LogoutHandler))
        handlers.append((r"/characters", CharacterHandler))
        handlers.append((r"/zone/(.*)/zone", CharacterZoneHandler))
        handlers.append((r"/characters", CharacterHandler))
        handlers.append((r"/objects", ObjectsHandler))
        handlers.append((r"/setstatus", CharStatusHandler))
        handlers.append((r"/movement", MovementHandler))
        return Application(handlers, cookie_secret=settings.COOKIE_SECRET)

    def test_everything(self):
        '''This is a test version of the 'idealclient.py' file for
        ease of automation.'''
        # Make sure the server is up.
        response = self.fetch('/ping').body
        expected = 'pong'
        self.assertEqual(expected, response)

        # Insert our user.
        user = User.query.filter_by(username=settings.DEFAULT_USERNAME, password=settings.DEFAULT_PASSWORD).first()
        if not user:
            User(username=settings.DEFAULT_USERNAME, password=settings.DEFAULT_PASSWORD)
            session.commit()

        # Log in.
        data = {'username':settings.DEFAULT_USERNAME, 'password':settings.DEFAULT_PASSWORD}
        response = self.fetch('/login', body=urlencode(data), method="POST")
        result = response.body
        expected = "Login successful."
        self.assertEqual(expected, result)

        cookie = response.headers['Set-Cookie']
        self.assertTrue(cookie)
        headers = {'Cookie': cookie}

        # Get our characters.
        response = self.fetch('/characters', headers=headers)
        result = json.loads(response.body)
        self.assertTrue(len(result) > 0)

        character = result[0]

        # Get the zone our character is in:
        response = self.fetch('/zone/%s/zone' % character, headers=headers)
        result = json.loads(response.body)
        expected = {'zone': 'playerinstance-GhibliHills-%s' % (character,)}
        self.assertEqual(result, expected)

        zone = result['zone']

        # Normally, the client would ask the masterzoneserver for the
        # url of the zone. This is not necessary for this test
        # since we already know where it is.

        # Get the zone's objects.
        response = self.fetch('/objects', headers=headers)

        self.fetch('/logout', headers=headers)

if __name__ == '__main__':
    unittest.main()
