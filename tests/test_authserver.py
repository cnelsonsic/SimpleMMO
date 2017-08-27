#!/usr/bin/env python2.7
import unittest

from tornado.web import Application

from mock import Mock, patch

import sys
sys.path.append(".")

import authserver
from authserver import AuthHandler, RegistrationHandler
import settings

class TestAuthHandler(unittest.TestCase):
    def setUp(self):
        app = Application([('/', AuthHandler)])
        req = Mock()
        self.auth_handler = AuthHandler(app, req)

        patch('authserver.UserController').start()

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
        MockUser.get = first

        # Test
        with patch.object(authserver, 'User', MockUser):
            result = self.auth_handler.authenticate(username, password)

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

        mock_set_secure_cookie.assert_called_once_with("user", user, domain=None)

    def test_set_current_user_with_none(self):
        user = None
        mock_clear_cookie = Mock()

        with patch.object(self.auth_handler, 'clear_cookie', mock_clear_cookie):
            self.auth_handler.set_current_user(user)

        mock_clear_cookie.assert_called_once_with("user")

class TestRegistrationHandler(unittest.TestCase):

    def setUp(self):
        app = Application([('/', RegistrationHandler)])
        req = Mock()
        self.auth_handler = RegistrationHandler(app, req)

        # Mock out the User and Session object
        self.MockUser = Mock()
        self.MockCommit = Mock()
        self.MockRollback = Mock()

        self.patches = []
        self.patches.append(patch.object(authserver, 'User', self.MockUser))
        self.patches.append(patch('elixir_models.db.commit', self.MockCommit))
        self.patches.append(patch('elixir_models.db.rollback', self.MockRollback))

        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()

    def test_register_user(self):
        self.MockUser.select().where().exists = Mock(return_value=False)

        # Test
        result = self.auth_handler.register_user("username", "password", "email")

        self.assertEqual(result, self.MockUser())

    def test_register_user_already_existing(self):
        from sqlalchemy.exc import IntegrityError
        self.MockCommit.side_effect = IntegrityError(None, None, None, None)

        # Test
        result = self.auth_handler.register_user("username", "password", "email")

        self.assertFalse(result)
        # self.assertEqual(self.MockSession.rollback.call_count, 1)


class TestCharacterHandler(unittest.TestCase):
    def test_get_characters(self):
        # character_handler = CharacterHandler()
        # self.assertEqual(expected, character_handler.get_characters(username))
        pass # TODO: implement your test here


if __name__ == '__main__':
    unittest.main()
