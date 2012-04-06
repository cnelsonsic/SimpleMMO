#!/usr/bin/env python2.7
import unittest

from tornado.web import Application, decode_signed_value
from tornado.testing import AsyncHTTPTestCase

from mock import Mock, patch

import sys
sys.path.append(".")

import authserver
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

# Some helpers for authentication:
def add_user(username, password):
    '''Add a user to the database.
    If it already exists, delete it first.
    Also mark it for cleanup later.'''
    delete_user(username, password)
    User(username=username, password=password)
    session.commit()

def delete_user(username, password):
    '''Delete a user from the database.'''
    User.query.filter_by(username=username, password=password).delete()
    session.commit()

def decode_cookies(response):
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

    def get_secure_cookie(self, name):
        '''A helper method to get a cookie that was set securely.'''
        for cookie in self.auth_handler._new_cookies:
            if name in cookie.keys():
                cookie_value = cookie[name].value
                result = decode_signed_value(settings.COOKIE_SECRET, name, cookie_value)
                return result

    def test_post(self):
        # Setup
        username = "gooduser"
        password = "goodpass"
        add_user(username, password)

        # Result: Sets user cookie, result will be 'Login Successful'
        qstring = "username=%s&password=%s" % (username, password)
        response = self.fetch('/', method='POST', body=qstring)
        expected = 'Login successful.'
        self.assertEqual(expected, response.body)

        # Check for cookies
        result = decode_cookies(response)
        self.assertEqual(None, result['admin'])
        self.assertEqual(username, result['user'])

    def test_post_bad_auth(self):
        # Setup
        username = "gooduser"
        goodpass = "goodpass"
        password = "badpass"
        add_user(username, goodpass)

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
            add_user(username, password)

            # Result: Sets user cookie, result will be 'Login Successful'
            qstring = "username=%s&password=%s" % (username, password)
            response = self.fetch('/', method='POST', body=qstring)
            expected = 'Login successful.'
            self.assertEqual(expected, response.body)

            # Check for cookies
            result = decode_cookies(response)
            self.assertEqual('true', result['admin'])
            self.assertEqual(username, result['user'])

class TestAuthHandlerUnit(unittest.TestCase):
    def setUp(self):
        app = Application([('/', AuthHandler)])
        req = Mock()
        self.auth_handler = AuthHandler(app, req)

    def test_authenticate(self):
        # Mock out the User object
        first = Mock(return_value=Mock())
        MockUser = Mock()
        MockUser.query.filter_by().first = first

        # Test
        with patch.object(authserver, 'User', MockUser):
            result = self.auth_handler.authenticate("username", "password")

        self.assertTrue(result)

    def test_authenticate_invalid_password(self):
        '''There is a good username and password in the database.
        But we give a real username, and a bad password.
        We should not be allowed to log in.'''
        username = "username"
        password = "password"

        # Mock out the User object
        MockUser = Mock()
        first = Mock(return_value=None)
        MockUser.query.filter_by().first = first

        # Test
        with patch.object(authserver, 'User', MockUser):
            result = self.auth_handler.authenticate(username, password)

        MockUser.query.filter_by.assert_called_with(username=username, password=password)
        first.assert_called_once_with()
        self.assertFalse(result)

    def test_set_admin(self):
        user = "user"
        MockAdmin = Mock()
        MockAdmin.__iter__ = Mock(return_value=iter([user]))
        mock_set_secure_cookie = Mock()

        with patch.object(settings, 'ADMINISTRATORS', MockAdmin):
            with patch.object(self.auth_handler, 'set_secure_cookie', mock_set_secure_cookie):
                self.auth_handler.set_admin(user)

        mock_set_secure_cookie.assert_called_once_with('admin', 'true')

    def test_set_admin_not_administrator(self):
        # Mock auth_handler.clear_cookie
        user = "user"
        MockAdmin = Mock()
        MockAdmin.__iter__ = Mock(return_value=iter([]))
        mock_clear_cookie = Mock()

        with patch.object(settings, 'ADMINISTRATORS', MockAdmin):
            with patch.object(self.auth_handler, 'clear_cookie', mock_clear_cookie):
                self.auth_handler.set_admin(user)

        mock_clear_cookie.assert_called_once_with('admin')

    def test_set_current_user(self):
        user = "username"
        mock_set_secure_cookie = Mock()

        with patch.object(self.auth_handler, 'set_secure_cookie', mock_set_secure_cookie):
            self.auth_handler.set_current_user(user)

        mock_set_secure_cookie.assert_called_once_with("user", user)

    def test_set_current_user_with_none(self):
        user = None
        mock_clear_cookie = Mock()

        with patch.object(self.auth_handler, 'clear_cookie', mock_clear_cookie):
            self.auth_handler.set_current_user(user)

        mock_clear_cookie.assert_called_once_with("user")


class TestLogoutHandler(unittest.TestCase):
    def test_get(self):
        # logout_handler = LogoutHandler()
        # self.assertEqual(expected, logout_handler.get())
        pass # TODO: implement your test here

class TestCharacterHandler(unittest.TestCase):
    def test_get_characters(self):
        # character_handler = CharacterHandler()
        # self.assertEqual(expected, character_handler.get_characters(username))
        pass # TODO: implement your test here

    def test_get(self):
        # character_handler = CharacterHandler()
        # self.assertEqual(expected, character_handler.get())
        pass # TODO: implement your test here

if __name__ == '__main__':
    unittest.main()
