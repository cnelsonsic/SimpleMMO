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

PROTOCOL = "http"
HOSTNAME = "localhost"

AUTHSERVERPORT = 1234
CHARSERVERPORT = 1235
MASTERZONESERVERPORT = 1236

import subprocess
COOKIE_SECRET = subprocess.check_output('git rev-parse HEAD', shell=True).strip()

AGPL_STRING = "BEGIN AGPL LICENSE BLOCK"
SKIP_FOLDERS = ("/.", ".git", ".svn", "/build/", "/srv/")

ZONESTARTPORT = 1300
ZONEENDPORT = 1400

ZONESTARTUPTIME = 10

MAX_ZONE_OBJECT_MESSAGE_COUNT = 1000

DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S:%f'

ADMINISTRATORS = ['admin']

CLIENT_TIMEOUT = 10 # Client gives up connecting after 10 seconds.

MSPERSEC = 1000
CLIENT_NETWORK_FPS = 10

CLIENT_UPDATE_FREQ = MSPERSEC/CLIENT_NETWORK_FPS
