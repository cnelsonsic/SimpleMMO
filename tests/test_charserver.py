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

import json
from mock import Mock

import sys
sys.path.append(".")

from elixir_models import setup as elixir_setup, User, Character

from playhouse.sqlite_ext import SqliteExtDatabase
from playhouse.test_utils import test_database

import settings
from charserver import CharacterZoneHandler

test_db = SqliteExtDatabase(':memory:', fields={'json':'json'})


class TestCharacterZoneHandler(AsyncHTTPTestCase):
    def get_app(self):
        return Application([('/(.*)/zone', CharacterZoneHandler)], cookie_secret=settings.COOKIE_SECRET)

    def setUp(self):
        super(TestCharacterZoneHandler, self).setUp()
        app = Application([('/(.*)/zone', CharacterZoneHandler)], cookie_secret=settings.COOKIE_SECRET)
        req = Mock()
        req.cookies = {}
        self.character_zone_handler = CharacterZoneHandler(app, req)

    def test_get(self):
        with test_database(test_db, (User, Character)):
            charname = "testcharname"
            result = json.loads(self.fetch('/%s/zone' % charname).body)
            expected = {'zone': 'playerinstance-GhibliHills-%s' % charname}
            self.assertEqual(result, expected)

    def test_get_zone(self):
        with test_database(test_db, (User, Character)):
            character = "testcharname"
            result = self.character_zone_handler.get_zone(character)
            expected = {'zone': 'playerinstance-GhibliHills-%s' % character}
            self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main()
