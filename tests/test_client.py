#!/usr/bin/env python2.7
import unittest

import sys
sys.path.append(".")

import settings

import client

authserver = None


class TestClient(unittest.TestCase):
    '''An integration test for the Client class.'''
    def setUp(self):
        pass

    @classmethod
    def setUpClass(cls):
        # Fire up a server to test against.
        import subprocess
        import requests
        cls.servers = []
        from collections import OrderedDict
        servers = OrderedDict()
        servers[settings.AUTHSERVER] = [sys.executable]+['authserver.py', '--dburi=sqlite://']
        servers[settings.CHARSERVER] = [sys.executable]+['charserver.py', '--dburi=sqlite://']
        servers['http://localhost:28017'] = ['mongod', '--rest', '--oplogSize=1', '--directoryperdb', '--smallfiles', '--dbpath=./mongodb-unittest/']
        servers[settings.ZONESERVER] = [sys.executable]+['masterzoneserver.py', '--dburi=sqlite://']
        for uri, args in servers.iteritems():
            if sys.executable in args:
                args.extend(['--log-file-prefix=log/%s.log' % args[1], '--logging=info'])
            print "Starting %s at %s" % (' '.join(args), uri)
            cmd = args
            s = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            cls.servers.append(s)
            status = None
            while status != 200:
                try:
                    r = requests.get(uri)
                    status = r.status_code
                except requests.ConnectionError:
                    continue

    @classmethod
    def tearDownClass(cls):
        from signal import SIGINT
        for server in cls.servers:
            server.send_signal(SIGINT)

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
        self.assertIn('Graxnor', c.characters)
        self.assertTrue(c.characters['Graxnor'])

    def test_get_zone(self):
        '''Client can get the zone for our character.'''
        c = client.Client(username=settings.DEFAULT_USERNAME, password=settings.DEFAULT_PASSWORD)
        self.assertTrue(c.get_zone('Graxnor'))

    def test_get_zone_cacheing(self):
        '''Client can get the zone for our character from the cache.'''
        c = client.Client(username=settings.DEFAULT_USERNAME, password=settings.DEFAULT_PASSWORD)
        self.assertTrue(c.get_zone('Graxnor'))
        expected = "Expected Zone"
        c.characters['Graxnor'].zone = expected
        result = c.get_zone('Graxnor')
        self.assertEqual(result, expected)

    def test_get_zone_url(self):
        '''Client can get the url for our character's zone.'''
        c = client.Client(username=settings.DEFAULT_USERNAME, password=settings.DEFAULT_PASSWORD)
        zoneid = c.get_zone('Graxnor')
        zoneurl = c.get_zone_url(zoneid)
        self.assertIn('http', zoneurl)

    def test_get_zone_url_no_args(self):
        '''Client can get the url for the last character's zone.'''
        c = client.Client(username=settings.DEFAULT_USERNAME, password=settings.DEFAULT_PASSWORD)
        zoneurl = c.get_zone_url()
        self.assertIn('http', zoneurl)

    def test_get_objects(self):
        '''Client can get the objects in our character's zone.'''
        c = client.Client(username=settings.DEFAULT_USERNAME, password=settings.DEFAULT_PASSWORD)
        c.get_objects()
        self.assertTrue(c.objects)

    def test_get_objects_verbose(self):
        '''Client can get the objects in our character's zone, when we give it.'''
        c = client.Client(username=settings.DEFAULT_USERNAME, password=settings.DEFAULT_PASSWORD)
        zoneid = c.get_zone('Graxnor')
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


if __name__ == '__main__':
    unittest.main()
