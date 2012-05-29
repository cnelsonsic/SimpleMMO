#!/usr/bin/env python2.7
import unittest

import sys
sys.path.append(".")

import settings

import client

from integration_base import IntegrationBase

class TestClient(IntegrationBase):

    @classmethod
    def setUpClass(cls):
        # Calling the supermethod so that we get servers.
        super(TestClient, cls).setUpClass()

        # Set the default character name.
        cls.character = 'Graxnor'

    def test___init__(self):
        '''Init the Client with no args.'''
        c = client.Client()
        self.assertTrue(c)

    def test___init___autoauth(self):
        '''Init the Client with a known good user/pass combo.'''
        c = client.Client(username=settings.DEFAULT_USERNAME, password=settings.DEFAULT_PASSWORD)
        self.assertTrue(c.cookies)
        self.assertTrue(c.cookies['user'])

    def test___init___autoauth_bad(self):
        '''Initting the Client with a bad user/pass combo will raise an exception. '''
        with self.assertRaises(client.AuthenticationError):
            client.Client(username="BadUser", password="BadPassword")

    def test_authenticate(self):
        '''Authenticating after initting Client should work.'''
        c = client.Client()
        result = c.authenticate(username=settings.DEFAULT_USERNAME, password=settings.DEFAULT_PASSWORD)
        self.assertTrue(result)
        self.assertTrue(c.cookies['user'])
        self.assertTrue(c.characters)

    def test_authenticate_after_auth(self):
        '''Authenticating after initting Client with auth should work.'''
        c = client.Client(username=settings.DEFAULT_USERNAME, password=settings.DEFAULT_PASSWORD)
        result = c.authenticate(username=settings.DEFAULT_USERNAME, password=settings.DEFAULT_PASSWORD)
        self.assertTrue(result)
        self.assertTrue(c.cookies['user'])

    def test_authenticate_bad(self):
        '''Authenticating with bad credentials after init does not succeed.'''
        c = client.Client()
        result = c.authenticate(username='BadUser', password='BadPassword')
        self.assertFalse(result)
        self.assertFalse(c.cookies)

    def test_characters(self):
        '''After authenticating, Client has a dictionary of characters.'''
        c = client.Client(username=settings.DEFAULT_USERNAME, password=settings.DEFAULT_PASSWORD)
        self.assertTrue(c.characters)
        self.assertIn(self.character, c.characters)
        self.assertTrue(c.characters[self.character])

    def test_get_zone(self):
        '''Client can get the zone for our character.'''
        c = client.Client(username=settings.DEFAULT_USERNAME, password=settings.DEFAULT_PASSWORD)
        self.assertTrue(c.get_zone(self.character))

    def test_get_zone_cacheing(self):
        '''Client can get the zone for our character from the cache.'''
        c = client.Client(username=settings.DEFAULT_USERNAME, password=settings.DEFAULT_PASSWORD)
        self.assertTrue(c.get_zone(self.character))
        expected = "Expected Zone"
        c.characters[self.character].zone = expected
        result = c.get_zone(self.character)
        self.assertEqual(result, expected)

    def test_get_zone_url(self):
        '''Client can get the url for our character's zone.'''
        c = client.Client(username=settings.DEFAULT_USERNAME, password=settings.DEFAULT_PASSWORD)
        zoneid = c.get_zone(self.character)
        zoneurl = c.get_zone_url(zoneid)
        self.assertIn('http', zoneurl)

    def test_get_zone_url_no_args(self):
        '''Client can get the url for the last character's zone.'''
        c = client.Client(username=settings.DEFAULT_USERNAME, password=settings.DEFAULT_PASSWORD)
        zoneurl = c.get_zone_url()
        self.assertIn('http', zoneurl)

    def test_get_zone_url_with_cache(self):
        '''Client can get the url for our character's zone from the cache'''
        c = client.Client(username=settings.DEFAULT_USERNAME, password=settings.DEFAULT_PASSWORD)
        zoneid = c.get_zone(self.character)
        c.get_zone_url(zoneid)

        expected = "Expected Zone Id"
        c.zones[zoneid] = expected

        result = c.get_zone_url(zoneid)
        self.assertEqual(result, expected)

    def test_get_objects(self):
        '''Client can get the objects in our character's zone.'''
        c = client.Client(username=settings.DEFAULT_USERNAME, password=settings.DEFAULT_PASSWORD)
        c.get_objects()
        self.assertTrue(c.objects)

    def test_get_objects_verbose(self):
        '''Client can get the objects in our character's zone, when we give it.'''
        c = client.Client(username=settings.DEFAULT_USERNAME, password=settings.DEFAULT_PASSWORD)
        zoneid = c.get_zone(self.character)
        zoneurl = c.get_zone_url(zoneid)
        c.get_objects(zoneurl)
        self.assertTrue(c.objects)

    def test_get_objects_update(self):
        '''Client can update its objects.'''
        c = client.Client(username=settings.DEFAULT_USERNAME, password=settings.DEFAULT_PASSWORD)
        c.get_objects()
        result = c.get_objects()
        self.assertTrue(c.objects)
        self.assertEqual(result, [], 'When updating that quickly, there should be no updated objects.')

    def test_set_character_status(self):
        '''Client can update its objects.'''
        c = client.Client(username=settings.DEFAULT_USERNAME, password=settings.DEFAULT_PASSWORD)
        c.get_zone_url(c.get_zone(self.character))
        c.get_objects()
        result = c.set_character_status(self.character, 'online')
        self.assertTrue(result)
        self.assertTrue(c.characters[self.character].online)

    def test_move_character(self):
        '''Client can move a character.'''
        c = client.Client(username=settings.DEFAULT_USERNAME, password=settings.DEFAULT_PASSWORD)
        character = self.character
        c.get_zone(character)
        c.set_character_status(character, 'online')
        result = c.move_character(character, 100, 100, 100)

        self.assertTrue(result)

    def test_move_character_bump(self):
        '''Client can try to move a character, but fail due to physics.'''
        c = client.Client(username=settings.DEFAULT_USERNAME, password=settings.DEFAULT_PASSWORD)
        character = self.character
        c.get_zone(character)
        c.set_character_status(character, 'online')
        result = c.move_character(character)

        self.assertFalse(result)

    def test_main(self):
        self.assertTrue(client.main(ticks=5))

    def test_activation(self):
        '''Client can activate an object.'''
        c = client.Client(username=settings.DEFAULT_USERNAME, password=settings.DEFAULT_PASSWORD)
        character = self.character
        print "testing using ", character
        # Override the character's zone:
        zone = 'playerinstance-AdventureDungeon-%s' % character
        c.characters[character].zone = zone
        c.set_online(character)

        c.get_objects()

        linnea = None
        for obj_id, obj in c.objects.iteritems():
            if obj.get('name') == 'Linnea':
                linnea = obj
                linnea_id = obj.get('_id', {}).get('$oid')
                break

        self.assertTrue(linnea)
        self.assertTrue(c.activate(linnea_id))


if __name__ == '__main__':
    unittest.main()
