#!/usr/bin/env python2.7
import unittest

from tornado.web import Application, decode_signed_value
from tornado.testing import AsyncHTTPTestCase

from mock import Mock

import sys
sys.path.append(".")

from authserver import PingHandler, AuthHandler, LogoutHandler, CharacterHandler
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

class TestPingHandler(AsyncHTTPTestCase):
    def get_app(self):
        return Application([('/', PingHandler)])

    def test_get(self):
        response = self.fetch('/').body
        expected = 'pong'
        self.assertEqual(expected, response)

class TestAuthHandler(AsyncHTTPTestCase):
    def get_app(self):
        return Application([('/', AuthHandler)], cookie_secret=settings.COOKIE_SECRET)

    def setUp(self):
        super(TestAuthHandler, self).setUp()
        set_up_db()
        app = Application([('/', AuthHandler)], cookie_secret=settings.COOKIE_SECRET)
        req = Mock()
        req.cookies = {}
        self.auth_handler = AuthHandler(app, req)

    def tearDown(self):
        super(TestAuthHandler, self).tearDown()

    def add_user(self, username, password):
        '''Add a user to the database.
        If it already exists, delete it first.
        Also mark it for cleanup later.'''
        self.delete_user(username, password)
        User(username=username, password=password)
        session.commit()

    def delete_user(self, username, password):
        '''Delete a user from the database.'''
        User.query.filter_by(username=username, password=password).delete()
        session.commit()

    def get_secure_cookie(self, name):
        '''A helper method to get a cookie that was set securely.'''
        for cookie in self.auth_handler._new_cookies:
            if name in cookie.keys():
                cookie_value = cookie[name].value
                result = decode_signed_value(settings.COOKIE_SECRET, name, cookie_value)
                return result

    def decode_cookies(self, response):
        '''Takes an HTTPResponse as the response.'''
        chunks = []
        for chunk in response.headers['Set-Cookie'].split(','):
            chunks.extend(chunk.split(';'))

        result = {}
        for chunk in chunks:
            s = chunk.split('=', 1)
            if len(s) < 2: continue
            name = s[0]
            value = s[1]
            result[name] = decode_signed_value(settings.COOKIE_SECRET, name, value.strip('"'))
        return result

    def test_authenticate(self):
        # Setup
        username = "gooduser"
        password = "goodpass"
        self.add_user(username, password)

        # Test
        expected = True
        result = self.auth_handler.authenticate(username, password)
        self.assertEqual(expected, result)

    def test_authenticate_invalid_password(self):
        '''There is a good username and password in the database.
        But we give a real username, and a bad password.
        We should not be allowed to log in.'''
        # Setup
        username = "gooduser"
        good_password = "goodpass"
        password = "badpassword"
        self.add_user(username, good_password)

        # Test
        expected = False
        result = self.auth_handler.authenticate(username, password)
        self.assertEqual(expected, result)

    def test_set_admin(self):
        for user in settings.ADMINISTRATORS:
            self.auth_handler.set_admin(user)

            # Check for cookies
            result = self.get_secure_cookie('admin')
            expected = 'true'
            self.assertEqual(expected, result)

    def test_set_admin_not_administrator(self):
        user = "gooduser"
        self.auth_handler.set_admin(user)

        # Check for cookies that were never set
        result = self.get_secure_cookie('admin')
        expected = None
        self.assertEqual(expected, result)

    def test_set_current_user(self):
        # Setup
        username = 'gooduser'

        # Test
        self.auth_handler.set_current_user(username)
        result = self.get_secure_cookie('user')
        expected = username
        self.assertEqual(expected, result)

    def test_set_current_user_with_none(self):
        # Setup
        username = None

        # Test
        self.auth_handler.set_current_user(username)
        result = self.get_secure_cookie('user')
        expected = username
        self.assertEqual(expected, result)

    def test_post(self):
        # Setup
        username = "gooduser"
        password = "goodpass"
        self.add_user(username, password)

        # Result: Sets user cookie, result will be 'Login Successful'
        qstring = "username=%s&password=%s" % (username, password)
        response = self.fetch('/', method='POST', body=qstring)
        expected = 'Login successful.'
        self.assertEqual(expected, response.body)

        # Check for cookies
        result = self.decode_cookies(response)
        self.assertEqual(None, result['admin'])
        self.assertEqual(username, result['user'])

    def test_post_bad_auth(self):
        # Setup
        username = "gooduser"
        goodpass = "goodpass"
        password = "badpass"
        self.add_user(username, goodpass)

        # Test
        qstring = "username=%s&password=%s" % (username, password)
        response = self.fetch('/', method='POST', body=qstring)
        expected = "401: Unauthorized"
        self.assertIn(expected, response.body)
        self.assertEqual(401, response.code)

    def test_post_admin(self):
        for username in settings.ADMINISTRATORS:
            # Setup
            password = "goodpass"
            self.add_user(username, password)

            # Result: Sets user cookie, result will be 'Login Successful'
            qstring = "username=%s&password=%s" % (username, password)
            response = self.fetch('/', method='POST', body=qstring)
            expected = 'Login successful.'
            self.assertEqual(expected, response.body)

            # Check for cookies
            result = self.decode_cookies(response)
            self.assertEqual('true', result['admin'])
            self.assertEqual(username, result['user'])

class TestLogoutHandler(unittest.TestCase):
    def test_get(self):
        # logout_handler = LogoutHandler()
        # self.assertEqual(expected, logout_handler.get())
        assert False # TODO: implement your test here

class TestCharacterHandler(unittest.TestCase):
    def test_get_characters(self):
        # character_handler = CharacterHandler()
        # self.assertEqual(expected, character_handler.get_characters(username))
        assert False # TODO: implement your test here

    def test_get(self):
        # character_handler = CharacterHandler()
        # self.assertEqual(expected, character_handler.get())
        assert False # TODO: implement your test here

if __name__ == '__main__':
    unittest.main()
