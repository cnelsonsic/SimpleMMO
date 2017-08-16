import unittest

import sys
sys.path.append(".")

from elixir_models import db, User, Character
from elixir_models import setup as elixir_models_setup

from playhouse.test_utils import test_database

from playhouse.sqlite_ext import SqliteExtDatabase
test_db = SqliteExtDatabase(':memory:')

class TestUser(unittest.TestCase):

    def test_init(self):
        '''Initting a User should work.'''
        tests = {'username': 'UserName',
                 'password':'Password',
                 'email': 'asdf@zxcv.sdf'}

        with test_database(test_db, (User, Character)):
            result = User.create(username="UserName",
                        password="Password",
                        email="asdf@zxcv.sdf")
            character = Character.create(name="Char", user=result)

            for attr, value in tests.iteritems():
                self.assertEqual(getattr(result, attr), value)
            self.assertEqual(result.characters[0], character)

    def test___repr__(self):
        user = User(username="Tim", characters=[Character(name="The Enchanter")])
        expected = '<User "Tim" owning character: The Enchanter.>'
        self.assertEqual(expected, user.__repr__())

class TestCharacter(unittest.TestCase):
    def test___repr__(self):
        # character = Character()
        # self.assertEqual(expected, character.__repr__())
        pass # TODO: implement your test here

class TestSetup(unittest.TestCase):
    def test_setup(self):
        # self.assertEqual(expected, setup(db_uri, echo))
        pass # TODO: implement your test here

if __name__ == '__main__':
    unittest.main()
