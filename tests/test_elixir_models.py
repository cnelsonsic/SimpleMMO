import unittest

import sys
sys.path.append(".")

from elixir_models import User, Character

class TestUser(unittest.TestCase):
    def test_init(self):
        '''Initting a User should work.'''
        characters = [Character()]
        tests = {'username': 'UserName',
                 'password':'Password',
                 'email': 'asdf@zxcv.sdf',
                 'characters': characters}

        result = User(username="UserName",
                      password="Password",
                      email="asdf@zxcv.sdf",
                      characters=characters)

        for attr, value in tests.iteritems():
            self.assertEqual(getattr(result, attr), value)

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
