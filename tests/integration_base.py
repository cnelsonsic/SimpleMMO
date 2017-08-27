
import subprocess
import requests
from collections import OrderedDict
from signal import SIGINT
import unittest

import os
import sys
sys.path.append(".")
import time

import settings

from elixir_models import setup as elixir_setup

class IntegrationBase(unittest.TestCase):
    '''An integration test for the Client class.'''

    @classmethod
    def setUpClass(cls):
        cls.servers = []

        # Wipe out the sqlite db.
        try:
            os.remove('testing.sqlite')
        except OSError:
            # Don't care if it doesn't exist
            pass

        elixir_setup(db_uri='testing.sqlite')

        # Fire up servers to test against.
        servers = OrderedDict()
        servers[settings.AUTHSERVER] = [sys.executable]+['authserver.py', '--dburi=testing.sqlite']
        servers[settings.CHARSERVER] = [sys.executable]+['charserver.py', '--dburi=testing.sqlite']
        servers[settings.ZONESERVER] = [sys.executable]+['masterzoneserver.py', '--dburi=testing.sqlite']
        for uri, args in servers.iteritems():
            if sys.executable in args:
                args.extend(['--log-file-prefix=log/%s.log' % args[1], '--logging=info'])
            cmd = args
            s = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            cls.servers.append(s)
            status = None
            tries = 0
            while status != 200:
                try:
                    r = requests.get(uri)
                    status = r.status_code
                    print r.text
                except requests.ConnectionError, e:
                    continue
                tries += 1
                time.sleep(0.1*tries)

    @classmethod
    def tearDownClass(cls):
        for server in cls.servers:
            server.send_signal(SIGINT)

        # Wipe out the sqlite db.
        try:
            os.remove('testing.sqlite')
        except OSError:
            # Don't care if it doesn't exist
            pass
