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

# Global Settings
PROTOCOL = "http"
HOSTNAME = "localhost"
_server_str = "%s://%s:%d"

AUTHSERVERPORT = 1234
CHARSERVERPORT = 1235
MASTERZONESERVERPORT = 1236
METASERVERPORT = 1237

AUTHSERVER = _server_str % (PROTOCOL, HOSTNAME, AUTHSERVERPORT)
CHARSERVER = _server_str % (PROTOCOL, HOSTNAME, CHARSERVERPORT)
ZONESERVER = _server_str % (PROTOCOL, HOSTNAME, MASTERZONESERVERPORT)
METASERVER = _server_str % (PROTOCOL, HOSTNAME, METASERVERPORT)

DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S:%f'

import subprocess
COOKIE_SECRET = subprocess.check_output('git rev-parse HEAD', shell=True).strip()

# Sentry DSN - Needs set up for your instance of Sentry
SENTRY = True
SENTRY_LOG = False # Sending log entries to sentry is slow and high-volume.
SENTRY_PORT = 9000
SENTRY_PUBLIC = '1a5305df80434b039a6e5030116b4c96'
SENTRY_PRIVATE = '28ce65222ae34a87b8a5c52a5d165c7d'
SENTRY_SERVER = _server_str % (PROTOCOL, HOSTNAME, SENTRY_PORT)
_dsn = "%s:%s@%s" % (SENTRY_PUBLIC, SENTRY_PRIVATE, HOSTNAME)
SENTRY_DSN = _server_str % (PROTOCOL, _dsn, 9000) + '/1'

# AGPL Stuff
AGPL_STRING = "BEGIN AGPL LICENSE BLOCK"
SKIP_FOLDERS = ("/.", ".git", ".svn", "/build/", "/srv/")

# AuthServer Settings
ADMINISTRATORS = ['admin']

# ZoneServer Settings
ZONESTARTPORT = 1300
ZONEENDPORT = 1400
ZONESTARTUPTIME = 10
DEFAULT_CHARACTER_ZONE = 'defaultzone'

SUPERVISORD = 'supervisord' # Constant
SUBPROCESS = 'subprocess' # Constant
START_ZONE_WITH = SUBPROCESS

# ScriptServer Settings
MAX_ZONE_OBJECT_MESSAGE_COUNT = 1000
MAX_DICE_AMOUNT = 100

# Client Settings
CLIENT_TIMEOUT = 10 # Client gives up connecting after 10 seconds.
MSPERSEC = 1000
CLIENT_NETWORK_FPS = 10
CLIENT_UPDATE_FREQ = MSPERSEC/CLIENT_NETWORK_FPS
DEFAULT_USERNAME = "Username"
DEFAULT_PASSWORD = "Password"
