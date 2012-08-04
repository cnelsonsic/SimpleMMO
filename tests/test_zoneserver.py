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

import datetime

from mock import Mock, patch

import sys
sys.path.append(".")

import zoneserver
from zoneserver import MovementHandler, CharacterController, ScriptedObjectHandler, DateLimitedObjectHandler

class TestCharacterControllerGetCharacter(unittest.TestCase):
    def setUp(self):
        self.character_controller = CharacterController()

    def test_get_character(self):
        mock_char = Mock(spec=['states'])
        MockCharacter = Mock()
        MockCharacter.objects().first = Mock(return_value=mock_char)

        with patch.object(zoneserver, 'Character', MockCharacter):
            result = self.character_controller.get_character("character")
        self.assertEqual(mock_char, result)

    def test_get_character_non_existent_empty_states(self):
        mock_char = Mock()
        mock_char.states = []
        MockCharacter = Mock()
        MockCharacter.objects().first = Mock(return_value=mock_char)

        with patch.object(zoneserver, 'Character', MockCharacter):
            result = self.character_controller.get_character("character")

        self.assertFalse(result)

    def test_get_character_non_existent_no_states(self):
        mock_char = Mock(name="char", spec=[])
        MockCharacter = Mock(name="Character")
        MockCharacter.objects().first = Mock(name="first", return_value=mock_char)

        with patch.object(zoneserver, 'Character', MockCharacter):
            result = self.character_controller.get_character("character")

        self.assertFalse(result)

class TestCharacterControllerSetCharacterStatus(unittest.TestCase):
    def setUp(self):
        self.character_controller = CharacterController()

    def test_set_char_status(self):
        mock_char = Mock(name="char")
        mock_char.states = ['alive']

        with patch.object(self.character_controller, 'create_character', Mock(return_value=mock_char)):
            result = self.character_controller.set_char_status("character", 'alive')

        self.assertEqual(result, mock_char)

    def test_set_char_status_with_new_state(self):
        mock_char = Mock(name="char")
        mock_char.states = []

        with patch.object(self.character_controller, 'create_character', Mock(return_value=mock_char)):
            self.character_controller.set_char_status("character", 'alive')

        self.assertTrue('alive' in mock_char.states)

    def test_set_char_status_mutually_exclusive(self):
        mock_char = Mock(name="char")
        mock_char.states = []

        with patch.object(self.character_controller, 'create_character', Mock(return_value=mock_char)):
            self.character_controller.set_char_status("character", 'online')

        self.assertTrue('online' in mock_char.states)

    def test_set_char_status_mutually_exclusive_flip(self):
        mock_char = Mock(name="char")
        mock_char.states = ['online']

        with patch.object(self.character_controller, 'create_character', Mock(return_value=mock_char)):
            self.character_controller.set_char_status("character", 'offline')

        self.assertTrue('offline' in mock_char.states)
        self.assertTrue('online' not in mock_char.states)

class TestCharacterControllerCreateCharacter(unittest.TestCase):
    def setUp(self):
        self.character_controller = CharacterController()

    def test_create_character(self):
        expected = Mock()

        with patch.object(self.character_controller, 'get_character', Mock(return_value=expected)):
            result = self.character_controller.create_character("character")

        self.assertEqual(result, expected)

    def test_create_character_with_new_charobj(self):
        mock_char = Mock(name="char", spec=[])
        mock_char.states = []
        MockCharacter = Mock(name="Character", return_value=mock_char)

        with patch.object(zoneserver, 'Character', MockCharacter):
            with patch.object(self.character_controller, 'get_character', Mock(return_value=None)):
                result = self.character_controller.create_character("character")

        self.assertEqual(result, mock_char)

class TestCharacterControllerSetMovement(unittest.TestCase):
    def setUp(self):
        self.character_controller = CharacterController()

        self.MockObject = Mock(name="Object")
        self.MockObject.objects = Mock(return_value=list())
        self.character_patch = patch.object(zoneserver, 'Object', self.MockObject)
        self.character_patch.start()

    def tearDown(self):
        self.character_patch.stop()

    def test_set_movement(self):
        mock_char = Mock(name="char", spec=['speed', 'save'])
        mock_char.speed = 1

        with patch.object(self.character_controller, 'create_character', Mock(return_value=mock_char)):
            result = self.character_controller.set_movement("character", 1, 2, 3)

        self.assertEqual(result.loc['x'], 0)

    def test_set_movement_existing_loc(self):
        mock_char = Mock(name="char")
        mock_char.speed = 1
        mock_char.loc = {'x': 0, 'y': 0, 'z': 0}

        with patch.object(self.character_controller, 'create_character', Mock(return_value=mock_char)):
            result = self.character_controller.set_movement("character", 1, 2, 3)

        self.assertGreater(result.loc['x'], 0)

    def test_set_movement_loc_is_none(self):
        mock_char = Mock(name="char")
        mock_char.speed = 1
        mock_char.loc = None

        with patch.object(self.character_controller, 'create_character', Mock(return_value=mock_char)):
            result = self.character_controller.set_movement("character", 1, 2, 3)

        self.assertEqual(result.loc['x'], 0)

    def test_set_movement_other_loc_is_none(self):
        '''When another object's loc is None,
        set_movement should not die horribly.'''
        mock_char = Mock(name="char")
        mock_char.speed = 1
        mock_char.loc = {'x': 0, 'y': 0, 'z': 0}

        mock_bad_obj = Mock()
        mock_bad_obj.loc = None

        MockObject = Mock()
        MockObject.objects = Mock(return_value=[mock_bad_obj])

        with patch.object(zoneserver, 'Object', MockObject):
            with patch.object(self.character_controller, 'create_character', Mock(return_value=mock_char)):
                result = self.character_controller.set_movement("character", 1, 2, 3)

        self.assertEqual(result.loc['x'], 1)

    def test_set_movement_physics_collision(self):
        mock_char = Mock(name="char")
        mock_char.speed = 1
        mock_char.loc = {'x': 0, 'y': 0, 'z': 0}

        self.MockObject.objects = Mock(return_value=[mock_char])

        with patch.object(zoneserver, 'Object', self.MockObject):
            with patch.object(self.character_controller, 'create_character', Mock(return_value=mock_char)):
                result = self.character_controller.set_movement("character", 1, 2, 3)

        self.assertFalse(result)

    def test_set_movement_physics_no_collision(self):
        mock_char = Mock(name="char")
        mock_char.speed = 1
        mock_char.loc = {'x': 0, 'y': 0, 'z': 0}

        mock_otherchar = Mock(name="other char")
        mock_otherchar.loc = {'x': 4, 'y': 4, 'z': 0}

        self.MockObject.objects = Mock(return_value=[mock_otherchar])

        with patch.object(zoneserver, 'Object', self.MockObject):
            with patch.object(self.character_controller, 'create_character', Mock(return_value=mock_char)):
                result = self.character_controller.set_movement("character", 1, 2, 3)

        self.assertEqual(result, mock_char)


class TestCharacterControllerIsOwner(unittest.TestCase):
    def setUp(self):
        self.character_controller = CharacterController()

    def test_is_owner(self):
        username = "username"
        character = "character"

        MockCharacter = Mock()
        MockCharacter.objects().first().owner = username
        with patch.object(zoneserver, 'Character', MockCharacter):
            result = self.character_controller.is_owner(username, character)

        self.assertTrue(result)

    def test_is_owner_no_char(self):
        username = "username"
        character = "character"

        MockCharacter = Mock()
        MockCharacter.objects().first = Mock(return_value=None)
        with patch.object(zoneserver, 'Character', MockCharacter):
            result = self.character_controller.is_owner(username, character)

        self.assertEqual(result, None)

class TestDateLimitedObjectHandlerUnit(unittest.TestCase):
    def setUp(self):
        self.app = Application([('/', DateLimitedObjectHandler),])
        self.req = Mock()
        self.objects_handler = DateLimitedObjectHandler(self.app, self.req)

    def test_get_objects(self):
        expected = []

        MockObject = Mock()
        MockObject.objects = expected
        with patch('zoneserver.DateLimitedObjectHandler.target_object', MockObject):
            result = self.objects_handler.get_objects()

        self.assertEqual(expected, result)

    def test_get_objects_with_since(self):
        expected = []

        MockObject = Mock()
        MockObject.objects = Mock(return_value=expected)
        with patch('zoneserver.DateLimitedObjectHandler.target_object', MockObject):
            result = self.objects_handler.get_objects(since=datetime.datetime.now())

        self.assertEqual(expected, result)

class TestMovementHandler(unittest.TestCase):
    def setUp(self):
        self.app = Application([('/', MovementHandler),])
        self.req = Mock()
        self.movement_handler = MovementHandler(self.app, self.req)

class TestWSMovementHandler(unittest.TestCase):
    def test_on_message(self):
        # w_s_movement_handler = WSMovementHandler()
        # self.assertEqual(expected, w_s_movement_handler.on_message(message))
        self.skipTest("Not Implemented.")

    def test_open(self):
        # w_s_movement_handler = WSMovementHandler()
        # self.assertEqual(expected, w_s_movement_handler.open())
        self.skipTest("Not Implemented.")

    def test_set_movement(self):
        # w_s_movement_handler = WSMovementHandler()
        # self.assertEqual(expected, w_s_movement_handler.set_movement(character, xmod, ymod, zmod))
        self.skipTest("Not Implemented.")

class TestAdminHandler(unittest.TestCase):
    def test___init__(self):
        # admin_handler = AdminHandler(*args, **kwargs)
        self.skipTest("Not Implemented.")

    def test_echo(self):
        # admin_handler = AdminHandler(*args, **kwargs)
        # self.assertEqual(expected, admin_handler.echo(arg))
        self.skipTest("Not Implemented.")

    def test_post(self):
        # admin_handler = AdminHandler(*args, **kwargs)
        # self.assertEqual(expected, admin_handler.post())
        self.skipTest("Not Implemented.")

class TestScriptedObjectHandler(unittest.TestCase):
    def setUp(self):
        self.app = Application([('/', ScriptedObjectHandler),])
        self.req = Mock()
        self.scripted_object_handler = ScriptedObjectHandler(self.app, self.req)

    def test_activate_object(self):
        mock_scripted_object = Mock()
        mock_scripted_object.scripts = ['games.objects.testscript']

        expected = [mock_scripted_object]

        MockScriptedObject = Mock()
        MockScriptedObject.objects.return_value = expected

        from games.objects.basescript import Script

        # Define a test class here because making Mock pass an issubclass
        # is a huge pain.
        class MyScript(Script):
            def activate(self, character):
                return expected[0]

        MockScriptModule = Mock(MyScript=MyScript, name='testscript')

        with patch.object(zoneserver, 'ScriptedObject', MockScriptedObject):
            with patch.dict('sys.modules', {'games.objects.testscript': MockScriptModule}):
                result = self.scripted_object_handler.activate_object(None, None)

        self.assertEqual(expected, result)

class TestMain(unittest.TestCase):
    def test_main(self):
        # self.assertEqual(expected, main(port))
        self.skipTest("Not Implemented.")

if __name__ == '__main__':
    unittest.main()
