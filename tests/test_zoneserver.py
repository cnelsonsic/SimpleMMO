#!/usr/bin/env python2.7
# ##### BEGIN AGPL LICENSE BLOCK #####
# This file is part of SimpleMMO.
#
# Copyright (C) 2011, 2012  Charles Nelson
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ##### END AGPL LICENSE BLOCK #####

import unittest
from tornado.web import Application
from tornado.testing import AsyncHTTPTestCase

import os
import shutil
import time
import subprocess
import datetime

import json
import mock
from mock import Mock

import sys
sys.path.append(".")

from elixir_models import metadata, setup_all, create_all

import settings
import zoneserver
ObjectsHandler = zoneserver.ObjectsHandler
from authserver import AuthHandler

def set_up_db():
    '''Connects to an in-memory SQLite database,
    with the purpose of emptying it and recreating it.'''
    metadata.bind = "sqlite:///:memory:"
#     metadata.bind.echo = True
    setup_all()
    create_all()

def set_user_cookie(app, request, username):
    from tornado.web import RequestHandler
    r = RequestHandler(app, request)
    r.set_secure_cookie('user', username)
    authcookie = r._new_cookies[0]
    cookiestring = authcookie.items()[0][1]
    request.cookies.update({'user': cookiestring})
    return request

class TestObjectsHandler(AsyncHTTPTestCase):
    def get_app(self):
        return Application([('/login', AuthHandler), ('/objects', ObjectsHandler),], cookie_secret=settings.COOKIE_SECRET)

    def setUp(self):
        super(TestObjectsHandler, self).setUp()
        set_up_db()
        self.app = self.get_app()
        self.req = Mock()
        self.req.cookies = {}
        self.objects_handler = ObjectsHandler(self.app, self.req)
        self.auth_handler = AuthHandler(self.app, self.req)

        self.zonename = "defaultzone"
        self.zoneid = "playerinstance-%s-username" % self.zonename

    def setup_mongo(self):
        import mongoengine as me
        try:
            me.connect(self.zoneid)
        except me.ConnectionError:
            self.skipTest("MongoDB server not running.")

        # Initialize the zone's setup things.
        from importlib import import_module
        zonemodule = import_module('games.zones.'+self.zonename)
        zonemodule.Zone()

    def tearDown(self):
        super(TestObjectsHandler, self).tearDown()

    def sign_in(self):
        '''Return a cookie that is suitable for authentication.'''
        self.setup_mongo()
        from test_authserver import add_user
        username = "username"
        password = "password"
        add_user(username, password)
        qstring = "username=%s&password=%s" % (username, password)
        authresponse = self.fetch('/login', method='POST', body=qstring)
        cookie = authresponse.headers['Set-Cookie']

        return cookie

    def test_head(self):
        #Setup:
        cookie = self.sign_in()

        #Test
        response = self.fetch('/objects', method='HEAD', headers={'Cookie':cookie})
        result = response.headers
        self.assertEqual(result['Cache-Control'], 'max-age=315360000')

    def test_get(self):
        '''By default, we should get some objects back.'''
        #Setup:
        cookie = self.sign_in()

        #Test
        response = self.fetch('/objects', method='GET', headers={'Cookie':cookie})
        result = json.loads(response.body)
        self.assertTrue(len(result) > 0)

    def test_get_objects(self):
        # Mock out the database's list of objects
        zoneserver.Object.objects = list()

        expected = []
        result = self.objects_handler.get_objects()
        self.assertEqual(expected, result)

    def test_get_objects_with_since(self):
        # Mock out the database's objects function.
        zoneserver.Object.objects = Mock(return_value=[])

        expected = []
        result = self.objects_handler.get_objects(since=datetime.datetime.now())
        self.assertEqual(expected, result)


class TestCharStatusHandler(unittest.TestCase):
    def test_post(self):
        # char_status_handler = CharStatusHandler()
        # self.assertEqual(expected, char_status_handler.post())
        pass # TODO: implement your test here

    def test_set_char_status(self):
        # char_status_handler = CharStatusHandler()
        # self.assertEqual(expected, char_status_handler.set_char_status(character, status))
        pass # TODO: implement your test here

    def test_get_character(self):
        # char_status_handler = CharStatusHandler()
        # self.assertEqual(expected, char_status_handler.get_character(character))
        pass # TODO: implement your test here

class TestMovementHandler(unittest.TestCase):
    def test_post(self):
        # movement_handler = MovementHandler()
        # self.assertEqual(expected, movement_handler.post())
        pass # TODO: implement your test here

    def test_set_movement(self):
        # movement_handler = MovementHandler()
        # self.assertEqual(expected, movement_handler.set_movement(character, xmod, ymod, zmod))
        pass # TODO: implement your test here

class TestWSMovementHandler(unittest.TestCase):
    def test_on_message(self):
        # w_s_movement_handler = WSMovementHandler()
        # self.assertEqual(expected, w_s_movement_handler.on_message(message))
        pass # TODO: implement your test here

    def test_open(self):
        # w_s_movement_handler = WSMovementHandler()
        # self.assertEqual(expected, w_s_movement_handler.open())
        pass # TODO: implement your test here

    def test_set_movement(self):
        # w_s_movement_handler = WSMovementHandler()
        # self.assertEqual(expected, w_s_movement_handler.set_movement(character, xmod, ymod, zmod))
        pass # TODO: implement your test here

class TestAdminHandler(unittest.TestCase):
    def test___init__(self):
        # admin_handler = AdminHandler(*args, **kwargs)
        pass # TODO: implement your test here

    def test_echo(self):
        # admin_handler = AdminHandler(*args, **kwargs)
        # self.assertEqual(expected, admin_handler.echo(arg))
        pass # TODO: implement your test here

    def test_post(self):
        # admin_handler = AdminHandler(*args, **kwargs)
        # self.assertEqual(expected, admin_handler.post())
        pass # TODO: implement your test here

class TestMain(unittest.TestCase):
    def test_main(self):
        # self.assertEqual(expected, main(port))
        pass # TODO: implement your test here

if __name__ == '__main__':
    unittest.main()
