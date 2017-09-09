#!/usr/bin/env python
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

import subprocess
import requests
import sys
import os
import logging

import docker
client = docker.from_env()

import settings

def start_zone(port=1300, zonename="defaultzone", instancetype="playerinstance", owner="Groxnor"):

    while True:
        try:
            # Check that the port isn't already taken
            url = settings._server_str % (settings.PROTOCOL, settings.HOSTNAME, port)
            requests.get(url)
        except requests.ConnectionError:
            # Port open!
            logging.info("Chose port %d" % port)
            break

        # "The door's locked. Move on to the next one."
        port += 1

    logging.info("Starting Zoneserver %s" % '-'.join((instancetype, zonename, owner)))
    logging.info("Server url: %s" % url)

    # Maybe --interactive and --tty
    container = client.containers.run(image='simplemmo-zoneserver',
                                        name='simplemmo-zoneserver-'+zonename,
                                        ports={port:port},
                                        environment={'PORT':port,
                                                    'INSTANCETYPE': instancetype,
                                                    'ZONENAME': zonename,
                                                    'OWNER': owner,
                                                    'LOGFILEPREFIX': 'log/simplemmo-zoneserver-%s.log' % '-'.join((instancetype, zonename, owner)),
                                                    'LOGLEVEL': 'info' },
                                        volumes={'/home/c/work/SimpleMMO/log': {'bind': '/SimpleMMO/log', 'mode': 'rw'}},
                                        detach=True,
                                        healthcheck={'test':'curl http://localhost:{}/'.format(port)}
                                        )

    for line in container.logs():
        logging.info("ZONE: {}".format(line))

    return container, url

def start_scriptserver(zonename="defaultzone", instancetype="playerinstance", owner="Groxnor"):

    args = ['scriptserver.py', '%s-%s-%s' % (instancetype, zonename, owner)]
    cmd = [sys.executable]+args
    logging.info("Starting %s" % ' '.join(args))
    s = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return s

if __name__ == "__main__":
    if start_zone():
        print "Started zone successfully."

