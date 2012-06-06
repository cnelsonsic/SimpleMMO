#!/usr/bin/env python2.7
import unittest

from tornado.web import Application, decode_signed_value
from tornado.testing import AsyncHTTPTestCase

from mock import Mock

import sys
sys.path.append(".")

from authserver import PingHandler, AuthHandler
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

class TestRegistrationHandler(AsyncHTTPTestCase):
    def get_app(self):
        return Application([('/', RegistrationHandler)], cookie_secret=settings.COOKIE_SECRET)

    def setUp(self):
        super(TestRegistrationHandler, self).setUp()
        set_up_db()
        app = Application([('/', RegistrationHandler)], cookie_secret=settings.COOKIE_SECRET)
        req = Mock()
        req.cookies = {}
        self.registration_handler = RegistrationHandler(app, req)

    def tearDown(self):
        super(TestAuthHandler, self).tearDown()

    def get_secure_cookie(self, name):
        '''A helper method to get a cookie that was set securely.'''
        for cookie in self.registration_handler._new_cookies:
            if name in cookie.keys():
                cookie_value = cookie[name].value
                result = decode_signed_value(settings.COOKIE_SECRET, name, cookie_value)
                return result

    def test_post(self):
        '''Create a user given an email, username and password.'''
        # Setup
        email = "user@example.com"
        username = "gooduser"
        password = "goodpass"

        # Result: Result will be 'Registration Successful', and a User will be created.
        qstring = "email={0}&username={1}&password={2}".format(email, username, password)
        response = self.fetch('/', method='POST', body=qstring)
        expected = 'Registration successful.'
        self.assertEqual(expected, response.body)

        # Check for User
        user = User.query.filter_by(username=username, password=password).one()
        self.assertTrue(user)
        self.assertEqual(user.email, email)

    def test_post_already_exists(self):
        '''Cannot create the same user twice.'''
        # Setup
        email = "user@example.com"
        username = "gooduser"
        password = "goodpass"

        # result: result will be 'registration successful', and a user will be created.
        qstring = "email={0}&username={1}&password={2}".format(email, username, password)
        response = self.fetch('/', method='post', body=qstring)
        expected = 'registration successful.'
        self.assertequal(expected, response.body)

        # Result: Result will be 'User already exists.'.
        response = self.fetch('/', method='POST', body=qstring)
        expected = 'User already exists.'
        self.assertEqual(expected, response.body)
        self.assertEqual(401, response.status)

    def test_post_no_username(self):
        '''Usernames are required.'''
        # Setup
        email = "user@example.com"
        password = "goodpass"

        # Result: Result will be 'A user name is required.'.
        qstring = "email={0}&password={1}".format(email, password)
        response = self.fetch('/', method='POST', body=qstring)
        expected = 'A user name is required.'
        self.assertEqual(expected, response.body)
        self.assertEqual(400, response.status)

    def test_post_no_password(self):
        '''Passwords are required.'''
        # Setup
        email = "user@example.com"
        username = "gooduser"

        # Result: Result will be 'A password is required.'.
        qstring = "email={0}&username={1}".format(email, username)
        response = self.fetch('/', method='POST', body=qstring)
        expected = 'A password is required.'
        self.assertEqual(expected, response.body)
        self.assertEqual(400, response.status)

    def test_post_no_email(self):
        '''Emails are optional.'''
        # Setup
        username = "gooduser"
        password = "goodpass"

        # Result: Result will be 'Registration Successful', and a User will be created.
        qstring = "username={0}&password={1}".format(username, password)
        response = self.fetch('/', method='POST', body=qstring)
        expected = 'Registration successful.'
        self.assertEqual(expected, response.body)

        # Check for User
        user = User.query.filter_by(username=username, password=password).one()
        self.assertTrue(user)

class TestLogoutHandler(unittest.TestCase):
    def test_get(self):
        # logout_handler = LogoutHandler()
        # self.assertEqual(expected, logout_handler.get())
        pass # TODO: implement your test here

class TestCharacterHandler(unittest.TestCase):

    def test_get(self):
        # character_handler = CharacterHandler()
        # self.assertEqual(expected, character_handler.get())
        pass # TODO: implement your test here

if __name__ == '__main__':
    unittest.main()
