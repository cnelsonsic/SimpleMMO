
import subprocess
import requests
from collections import OrderedDict
from signal import SIGINT
import unittest

import os
import sys
sys.path.append(".")

import settings


class IntegrationBase(unittest.TestCase):
    '''An integration test for the Client class.'''

    @classmethod
    def setUpClass(cls):
        # Fire up servers to test against.
        cls.servers = []
        servers = OrderedDict()
        cls.mongodb_dir = './mongodb-unittest/'
        if not os.path.exists(cls.mongodb_dir):
            os.mkdir(cls.mongodb_dir)
        servers['http://localhost:28017'] = ['mongod', '--rest', '--oplogSize=1', '--directoryperdb', '--smallfiles', '--dbpath=%s' % cls.mongodb_dir]
        servers[settings.AUTHSERVER] = [sys.executable]+['authserver.py', '--dburi=sqlite://']
        servers[settings.CHARSERVER] = [sys.executable]+['charserver.py', '--dburi=sqlite://']
        servers[settings.ZONESERVER] = [sys.executable]+['masterzoneserver.py', '--dburi=sqlite://']
        for uri, args in servers.iteritems():
            if sys.executable in args:
                args.extend(['--log-file-prefix=log/%s.log' % args[1], '--logging=info'])
            cmd = args
            s = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            cls.servers.append(s)
            status = None
            while status != 200:
                try:
                    r = requests.get(uri)
                    status = r.status_code
                except requests.ConnectionError:
                    continue

    @classmethod
    def tearDownClass(cls):
        for server in cls.servers:
            server.send_signal(SIGINT)
        import shutil
        shutil.rmtree(cls.mongodb_dir)
