#!/usr/bin/env python
'''ZoneScriptServer
A server that runs scripts for all the objects in a zone.
'''

import threading
from threading import Timer

import sched, time
s = sched.scheduler(time.time, time.sleep)

from settings import CLIENT_UPDATE_FREQ

class ZoneScriptRunner(object):
    '''This is a class that holds all sorts of methods for running scripts for
    a zone. It does not talk to the HTTP handler(s) directly, but instead uses
    the same database. It might take player movement updates directly in the
    future for speed, but this is unlikely.'''

    def __init__(self):
        self.scriptnames = []
        self.scripts = {}

        # Query DB for a list of all objects' script names,
        #   ordered according to proximity to players
        # Store list of script names in self
        # For each script name in the list:
        #   Import those by name via __import__
        #   For each class object in each one's dir()
        #       call class()
        #       store object instance in a dict like {scriptname: classinstance}

    def tick(self):
        '''Iterate through all known scripts and call their tick method.'''
        # Tick all the things
        print "tick"
        for script in self.scriptnames:
            # TODO: Pass some locals or somesuch so that they can query the db
            self.scripts[script].tick()


    def start(self):
        print "Running scriptserver"

        dilation = 1.0
        maxframelen = (CLIENT_UPDATE_FREQ/200.0)
        print "Max frame length is %f seconds." % maxframelen

        lasttick = time.time()

        while True:
            maxframelength = maxframelen*dilation

            # If there are too many scripts running that are taking up too many
            # resources, change the time dilation so that they have more time to
            # run before the next loop.
            # This may not be needed since ScriptServer is a separate process.
            utilization = (time.time()-lasttick)/maxframelength
            if utilization > 1:
                dilation = dilation*1.05
                print "Changing dilation to %f" % dilation
            elif utilization < 0.80:
                dilation = dilation*0.95
                print "Changing dilation to %f" % dilation

            # Max frame length minus the Time taken ticking is how much to sleep
            # 0.10s - (0.03s) = sleep for 0.7s.
            sleeptime = max(maxframelength-(time.time()-lasttick), 0)
            print "Sleeping for %f seconds. (%3.4f%% utilization.)" % (sleeptime, utilization*100)
            time.sleep(sleeptime)

            # TODO: Trigger any events for scripts. May need some more DB queries.
            #   TODO: Trigger object proximity events, scripts can filter down to players

            # Finally, tick all the scripts.
            self.tick()
            lasttick = time.time()


if __name__ == "__main__":
    zsr = ZoneScriptRunner()
    zsr.start()
