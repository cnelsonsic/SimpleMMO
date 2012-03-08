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

import xmlrpclib
import supervisor
from supervisor.xmlrpc import SupervisorTransport

from settings import ZONESTARTPORT, ZONEENDPORT

from elixir_models import Zone, session

def _add_process(twiddlerproxy, processgroup, zoneid, settings, port):
    '''Adds a zone process to supervisor and does some checks to only start it
    if it isn't already running, and restart it if it's not.'''

    s = twiddlerproxy
    try:
        retval = s.twiddler.addProgramToGroup(processgroup, zoneid, settings)

        print "Added successfully."

        zone = Zone.query.filter_by(zoneid=zoneid).first()
        if zone:
            # This zone already exists, so update the port number.
            zone.port = port
        else:
            # This zone doesn't exist. Create a new one.
            Zone(zoneid=zoneid, port=port)
        session.commit()

    except(xmlrpclib.Fault), exc:
        if "BAD_NAME" in exc.faultString:
            try:
                # Zone crashed, remove it from the process list.
                s.twiddler.removeProcessFromGroup(processgroup, zoneid)
            except(xmlrpclib.Fault), exc:
                if "STILL_RUNNING" in exc.faultString:
                    # Process still running just fine, return true.
                    print "Still running, leaving it alone."
                    retval = True
            else:
                print "Restarting stopped/crashed zone."
                # Removing the process worked, delete the zone from the database.
                Zone.query.filter_by(zoneid=zoneid).delete()
                session.commit()
                # Start zone again
                retval = _add_process(s, processgroup, zoneid, settings, port)
        else:
            print exc
            print exc.faultCode, exc.faultString
            raise
    finally:
        session.commit()
        return retval

def start_zone(port=1300, zonename="defaultzone", instancetype="playerinstance", owner="Groxnor", processgroup='zones', autorestart=False):
    s = xmlrpclib.ServerProxy('http://localhost:9001')

    import socket
    try:
        version = s.twiddler.getAPIVersion()
    except(socket.error), exc:
        raise UserWarning("Could not connect to supervisor: %s" % exc)

    if float(version) >= 0.3:
        # Query through all our zones to get a good port number.
        taken_ports = [p[0] for p in session.query(Zone.port).all()]
        for port in xrange(ZONESTARTPORT, ZONEENDPORT):
            if port not in taken_ports:
                break
        print "Chose port # %d" % port

        command = '/usr/bin/python zoneserver.py --port=%d --zonename=%s --instancetype=%s --owner=%s' % (int(port), zonename, instancetype, owner)
        zoneid = '-'.join((instancetype, zonename, owner))
        settings = {'command': command, 'autostart': str(True), 'autorestart': str(autorestart), 'redirect_stderr': str(True)}
        addtogroup = _add_process(s, processgroup, zoneid, settings, port)

        # Start up a scriptserver:
        settings['command'] = '/usr/bin/python scriptserver.py %s' % zoneid
        zonescriptserver = _add_process(s, processgroup, zoneid+"-scriptserver", settings, 1)

        if addtogroup:
            from settings import PROTOCOL, HOSTNAME
            serverurl = "%s://%s:%d" % (PROTOCOL, HOSTNAME, port)
            return serverurl
        else:
            raise UserWarning("Couldn't add zone %s to process group." % zoneid)
    else:
        raise UserWarning("Twiddler version too old.")


if __name__ == "__main__":
    if start_zone():
        print "Started zone successfully."

