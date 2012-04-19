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
import logging

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

    args = ['zoneserver.py', '--port=%d' % port,
                                '--instancetype=%s' % instancetype,
                                '--zonename=%s' % zonename,
                                '--owner=%s' % owner]
    cmd = [sys.executable]+args
    logging.info("Starting %s" % ' '.join(args))
    logging.info("Server url: %s" % url)
    s = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return s, url

if __name__ == "__main__":
    if start_zone():
        print "Started zone successfully."

