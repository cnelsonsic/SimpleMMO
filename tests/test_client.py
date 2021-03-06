#!/usr/bin/env python2.7
from contextlib import contextmanager
import unittest

import logging
logging.getLogger('requests.packages.urllib3.connectionpool').setLevel(logging.WARN)

import sys
sys.path.append(".")

import time

import settings

import clientlib

from integration_base import IntegrationBase

from elixir_models import setup as elixir_setup, User, Character

from playhouse.sqlite_ext import SqliteExtDatabase
from playhouse.test_utils import test_database

import unittest

class TestClient(IntegrationBase):

    @classmethod
    def setUpClass(cls):
        # Calling the supermethod so that we get servers.
        print "Calling setupclass"
        super(TestClient, cls).setUpClass()

        # c = clientlib.Client(username=settings.DEFAULT_USERNAME, password=settings.DEFAULT_PASSWORD)
        # cls.character = c.create_character('Graxnor')

    @contextmanager
    def fresh_servers(self):
        '''Kills all the servers and restarts them.'''
        self.tearDownClass() # Kill off all the existing servers
        self.setUpClass() # Fire up new servers
        # self.mysetUp()
        yield # Let the code do its thing
        self.tearDownClass() # Kill off the existing servers
        self.setUpClass() # Fire up new servers for the next test

    def test___init__(self):
        '''Init the Client with no args.'''
        c = clientlib.Client()
        self.assertTrue(c)

    def test___init___autoauth(self):
        '''Init the Client with a known good user/pass combo.'''
        with self.fresh_servers():
            c = clientlib.Client(username=settings.DEFAULT_USERNAME, password=settings.DEFAULT_PASSWORD)
        self.assertTrue(c.cookies)
        self.assertTrue(c.cookies['user'])

    def test___init___autoauth_bad(self):
        '''Initting the Client with a bad user/pass combo will raise an exception. '''
        with self.assertRaises(clientlib.AuthenticationError):
            clientlib.Client(username="BadUser", password="BadPassword")

    def test_register(self):
        '''Register with a good username and password.'''
        c = clientlib.Client()
        with self.fresh_servers():
            result = c.register(username="gooduser", password="goodpass", email="test@example.com")
        self.assertTrue(result)
        self.assertEqual(c.last_user, "gooduser")

    def test_register_twice(self):
        '''Register with a good username and password, twice!
        If a user tries to register twice, with the same info, their request
        should be squelched and all continues as if nothing went awry.
        (If the user re-instantiates the client, show errors as normal.)
        '''
        c = clientlib.Client()
        with self.fresh_servers():
            first_result = c.register(username="gooduser", password="goodpass", email="test@example.com")
            self.assertTrue(first_result)
            self.assertEqual(c.last_user, "gooduser")

            second_result = c.register(username="gooduser", password="goodpass", email="test@example.com")
            self.assertTrue(second_result)

    def test_register_twice_different_instance(self):
        '''Register a good username and password twice, from different instances.
        If a user tries to register a username that is already taken, show them
        a meaningful error.'''
        c = clientlib.Client()
        with self.fresh_servers():
            result = c.register(username="gooduser", password="goodpass", email="test@example.com")
            self.assertTrue(result)

            c = clientlib.Client()
            with self.assertRaises(clientlib.RegistrationError) as cm:
                c.register(username="gooduser", password="goodpass", email="test@example.com")
            self.assertIn('User already exists.', cm.exception.message)

    def test_create(self):
        '''Create a character.
        Not only must the create_character function return the character name
        the server created, but also update the client's characters dict.'''
        with self.fresh_servers():
            c = clientlib.Client(username=settings.DEFAULT_USERNAME, password=settings.DEFAULT_PASSWORD)
            expected = "Cuddlepums"
            result = c.create_character(character_name=expected)
        self.assertEqual(result, expected)
        self.assertIn(expected, c.characters)

    def test_ping(self):
        '''Pinging the authserver should work.'''
        with self.fresh_servers():
            c = clientlib.Client()
            result = c.ping()
        self.assertTrue(result)

    def test_bad_ping(self):
        '''Pinging a bogus authserver should return False.'''
        oldserver = settings.AUTHSERVER
        clientlib.settings.AUTHSERVER = "http://127.0.0.1:53000"
        c = clientlib.Client()
        result = c.ping()
        self.assertFalse(result)
        clientlib.settings.AUTHSERVER = oldserver

    def test_authenticate(self):
        '''Authenticating after initting Client should work.'''
        c = clientlib.Client()
        with self.fresh_servers():
            result = c.authenticate(username=settings.DEFAULT_USERNAME, password=settings.DEFAULT_PASSWORD)
            self.character = c.create_character('Graxnor')
        self.assertTrue(result)
        self.assertTrue(c.cookies['user'])
        self.assertTrue(c.characters)

    def test_authenticate_after_auth(self):
        '''Authenticating after initting Client with auth should work.'''
        with self.fresh_servers():
            c = clientlib.Client(username=settings.DEFAULT_USERNAME, password=settings.DEFAULT_PASSWORD)
            result = c.authenticate(username=settings.DEFAULT_USERNAME, password=settings.DEFAULT_PASSWORD)
        self.assertTrue(result)
        self.assertTrue(c.cookies['user'])

    def test_authenticate_bad(self):
        '''Authenticating with bad credentials after init does not succeed.'''
        with self.fresh_servers():
            c = clientlib.Client()
            result = c.authenticate(username='BadUser', password='BadPassword')
        self.assertFalse(result)
        self.assertFalse(c.cookies)

    def test_characters(self):
        '''After authenticating, Client has a dictionary of characters.'''
        with self.fresh_servers():
            c = clientlib.Client(username=settings.DEFAULT_USERNAME, password=settings.DEFAULT_PASSWORD)
            self.character = c.create_character('Graxnor')
        self.assertTrue(c.characters)
        self.assertIn(self.character, c.characters)
        self.assertTrue(c.characters[self.character])

    def test_get_zone(self):
        '''Client can get the zone for our character.'''
        with self.fresh_servers():
            c = clientlib.Client(username=settings.DEFAULT_USERNAME, password=settings.DEFAULT_PASSWORD)
            self.character = c.create_character('Graxnor')
            self.assertTrue(c.get_zone(self.character))

    def test_get_zone_cacheing(self):
        '''Client can get the zone for our character from the cache.'''
        with self.fresh_servers():
            c = clientlib.Client(username=settings.DEFAULT_USERNAME, password=settings.DEFAULT_PASSWORD)
            self.character = c.create_character('Graxnor')
            self.assertTrue(c.get_zone(self.character))
            expected = "Expected Zone"
            c.characters[self.character].zone = expected
            result = c.get_zone(self.character)
        self.assertEqual(result, expected)

    def test_get_zone_url(self):
        '''Client can get the url for our character's zone.'''
        with self.fresh_servers():
            c = clientlib.Client(username=settings.DEFAULT_USERNAME, password=settings.DEFAULT_PASSWORD)
            self.character = c.create_character('Graxnor')
            zoneid = c.get_zone(self.character)
            zoneurl = c.get_zone_url(zoneid)
        self.assertIn('http', zoneurl)

    def test_get_zone_url_no_args(self):
        '''Client can get the url for the last character's zone.'''
        with self.fresh_servers():
            c = clientlib.Client(username=settings.DEFAULT_USERNAME, password=settings.DEFAULT_PASSWORD)
            self.character = c.create_character('Graxnor')
            zoneurl = c.get_zone_url()
        self.assertIn('http', zoneurl)

    def test_get_zone_url_with_cache(self):
        '''Client can get the url for our character's zone from the cache'''
        with self.fresh_servers():
            c = clientlib.Client(username=settings.DEFAULT_USERNAME, password=settings.DEFAULT_PASSWORD)
            self.character = c.create_character('Graxnor')
            zoneid = c.get_zone(self.character)
            c.get_zone_url(zoneid)

            expected = "Expected Zone Id"
            c.zones[zoneid] = expected

            result = c.get_zone_url(zoneid)
        self.assertEqual(result, expected)

    def test_get_objects(self):
        '''Client can get the objects in our character's zone.'''
        with self.fresh_servers():
            c = clientlib.Client(username=settings.DEFAULT_USERNAME, password=settings.DEFAULT_PASSWORD)
            self.character = c.create_character('Graxnor')
            print c.get_objects()
        self.assertTrue(c.objects)
        print c.objects

    def test_get_objects_verbose(self):
        '''Client can get the objects in our character's zone, when we give it.'''
        with self.fresh_servers():
            c = clientlib.Client(username=settings.DEFAULT_USERNAME, password=settings.DEFAULT_PASSWORD)
            self.character = c.create_character('Graxnor')
            zoneid = c.get_zone(self.character)
            zoneurl = c.get_zone_url(zoneid)
            c.get_objects(zoneurl)
        self.assertTrue(c.objects)

    def test_get_objects_update(self):
        '''Client can update its objects.'''
        with self.fresh_servers():
            c = clientlib.Client(username=settings.DEFAULT_USERNAME, password=settings.DEFAULT_PASSWORD)
            self.character = c.create_character('Graxnor')
            self.assertEqual(len(c.objects), 0) 
            orig_objs = c.get_objects()
            result = c.get_objects()

        self.assertEqual(len(c.objects), 11) 
        self.assertEqual(len(result), 0, 'When updating that quickly, there should be no updated objects. {}'.format(str(result)))

    def test_set_character_status(self):
        '''Client can update its objects.'''
        with self.fresh_servers():
            c = clientlib.Client(username=settings.DEFAULT_USERNAME, password=settings.DEFAULT_PASSWORD)
            self.character = c.create_character('Graxnor')
            c.get_objects()
            result = c.set_character_status(self.character, 'online')
        self.assertTrue(result)
        self.assertTrue(c.characters[self.character].online)

    def test_move_character(self):
        '''Client can move a character.'''
        with self.fresh_servers():
            c = clientlib.Client(username=settings.DEFAULT_USERNAME, password=settings.DEFAULT_PASSWORD)
            character = c.create_character('Graxnor')
            c.set_character_status(character, 'online')
            result = c.move_character(character, 100, 100, 100)

        self.assertTrue(result)

    def test_move_character_bump(self):
        '''Client can try to move a character, but fail due to physics.'''
        with self.fresh_servers():
            c = clientlib.Client(username=settings.DEFAULT_USERNAME, password=settings.DEFAULT_PASSWORD)
            character = c.create_character('Graxnor')
            c.set_character_status(character, 'online')
            result = c.move_character(character)

        self.assertFalse(result)

    def test_main(self):
        self.assertTrue(clientlib.main(ticks=5))

    def get_linnea(self, objects):
        linnea = None
        for obj_id, obj in objects.iteritems():
            if obj.get('name') == 'Linnea':
                linnea = obj
                break

        return linnea


    def test_activation(self):
        '''Client can activate an object.'''
        with self.fresh_servers():
            c = clientlib.Client(username=settings.DEFAULT_USERNAME, password=settings.DEFAULT_PASSWORD)
            character = c.create_character('Graxnor')
            print "testing using ", character
            # Override the character's zone:
            zone = 'playerinstance-AdventureDungeon-%s' % character
            c.characters[character].zone = zone
            c.set_online(character)

            c.get_objects()

            linnea = self.get_linnea(c.objects)

            self.assertTrue(linnea)
            self.assertTrue(c.activate(linnea['id']))

    def test_scriptserver(self):
        '''Client can see the ScriptServer updating objects.'''
        with self.fresh_servers():
            c = clientlib.Client(username=settings.DEFAULT_USERNAME, password=settings.DEFAULT_PASSWORD)
            character = c.create_character('Graxnor')
            # Override the character's zone:
            zone = 'playerinstance-AdventureDungeon-%s' % character
            c.characters[character].zone = zone
            c.set_online(character)

            print c.get_objects()

            linnea = self.get_linnea(c.objects)

            # Wait a bit for Linnea to wander about.
            time.sleep(0.1)

            c.get_objects()
            updated_linnea = self.get_linnea(c.objects)

        self.assertTrue(updated_linnea)
        self.assertNotEqual(linnea, updated_linnea)
        self.assertNotEqual(linnea['last_modified'], updated_linnea['last_modified'])

        # Any of the three x, y and z values should not match.
        matches = any([linnea['loc_%s'%attr] != updated_linnea['loc_%s'%attr] for attr in ('x', 'y', 'z')])
        self.assertTrue(matches)

    def test_get_messages(self):
        with self.fresh_servers():
            c = clientlib.Client(username=settings.DEFAULT_USERNAME, password=settings.DEFAULT_PASSWORD)
            character = c.create_character('Graxnor')
            # Override the character's zone:
            zone = 'playerinstance-AdventureDungeon-%s' % character
            c.characters[character].zone = zone
            c.set_online(character)
            c.get_objects()

            # Poke Linnea to make her talk
            linnea = self.get_linnea(c.objects)
            c.activate(linnea['id'])

            c.get_messages()

        self.assertTrue(c.messages)



if __name__ == '__main__':
    unittest.main()
