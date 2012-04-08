#!/usr/bin/env python2.7
import unittest

from tornado.web import Application

from mock import Mock, patch

import sys
sys.path.append(".")

import authserver
from authserver import AuthHandler
import settings

class TestAuthHandler(unittest.TestCase):
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

class TestCharacterHandler(unittest.TestCase):
    def test_get_characters(self):
        # character_handler = CharacterHandler()
        # self.assertEqual(expected, character_handler.get_characters(username))
        pass # TODO: implement your test here


if __name__ == '__main__':
    unittest.main()
