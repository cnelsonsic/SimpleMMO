import xmlrpclib
from supervisor.xmlrpc import SupervisorTransport

def start_zone(port=1300, zoneid="defaultzone", processgroup='zones', autorestart=False):
    s = xmlrpclib.ServerProxy('http://localhost:9001')

    import socket
    try:
        version = s.twiddler.getAPIVersion()
    except(socket.error), exc:
        raise UserWarning("Could not connect to supervisor: %s" % exc)

    if float(version) >= 0.3:
        command = '/usr/bin/python zoneserver.py --port=%d --zoneid=%s' % (port, zoneid)
        settings = {'command': command, 'autostart': str(True), 'autorestart': str(autorestart)}
        try:
            addtogroup = s.twiddler.addProgramToGroup(processgroup, zoneid, settings)
        except(xmlrpclib.Fault), exc:
            if "BAD_NAME" in exc.faultString:
                raise UserWarning("Zone already exists in process list.")
            else:
                print exc
                print exc.faultCode, exc.faultString
                raise

        if addtogroup:
            return True
        else:
            raise UserWarning("Couldn't add zone %s to process group." % zoneid)
    else:
        raise UserWarning("Twiddler version too old.")


if __name__ == "__main__":
    if start_zone():
        print "Started zone successfully."

