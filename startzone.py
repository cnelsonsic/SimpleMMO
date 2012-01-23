import xmlrpclib
import supervisor
from supervisor.xmlrpc import SupervisorTransport

def _add_process(twiddlerproxy, processgroup, zoneid, settings):
    '''Adds a zone process to supervisor and does some checks to only start it
    if it isn't already running, and restart it if it's not.'''

    s = twiddlerproxy
    try:
        retval = s.twiddler.addProgramToGroup(processgroup, zoneid, settings)
        print "Added successfully."
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
                # Start zone again
                retval = _add_process(s, processgroup, zoneid, settings)
        else:
            print exc
            print exc.faultCode, exc.faultString
            raise
    finally:
        return retval

def start_zone(port=1300, zoneid="defaultzone", processgroup='zones', autorestart=False):
    s = xmlrpclib.ServerProxy('http://localhost:9001')

    import socket
    try:
        version = s.twiddler.getAPIVersion()
    except(socket.error), exc:
        raise UserWarning("Could not connect to supervisor: %s" % exc)

    if float(version) >= 0.3:
        command = '/usr/bin/python zoneserver.py --port=%d --zoneid=%s' % (int(port), zoneid)
        settings = {'command': command, 'autostart': str(True), 'autorestart': str(autorestart), 'redirect_stderr': str(True)}
        addtogroup = _add_process(s, processgroup, zoneid, settings)

        if addtogroup:
            return True
        else:
            raise UserWarning("Couldn't add zone %s to process group." % zoneid)
    else:
        raise UserWarning("Twiddler version too old.")


if __name__ == "__main__":
    if start_zone():
        print "Started zone successfully."

