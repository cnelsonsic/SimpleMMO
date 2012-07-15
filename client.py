#!/usr/bin/env python2.7
from __future__ import division
from datetime import datetime
from pprint import pformat
from cmd2 import Cmd, options, make_option
import logging
logging.basicConfig()
# We don't care about clientlib logging.
logging.getLogger('clientlib').setLevel(logging.CRITICAL)
import clientlib
import settings

class InteractiveClient(Cmd):
    client = clientlib.Client()
    quiet = False
    debug = True
    prompt = " > "

    def format_prompt(self, username='', character='', zone=''):
        if not username:
            username = self.client.last_user
        if not character:
            character = self.client.last_character
        if not zone:
            # We want the actual name of the zone instead of the url.
            for zoneid, zone in self.client.zones.iteritems():
                if zone == self.client.last_zone:
                    # The instance type and instance owner are implied,
                    # So we only want the actual zone name.
                    zone = zoneid.split('-')[1]
                    break
            zone = '@{0}'.format(zone) if zone else ''

        retval = "{username}:{character}{zone}> ".format(username=username, character=character, zone=zone)
        self.prompt = retval
        return retval

    def logged_in(self):
        if not self.client.last_character:
            self.perror("You are not logged in. Use 'login' to authenticate.")
            return False
        else:
            return True

    @options([make_option('-u', '--username', type="string", help="The name of the user you want to register."),
              make_option('-p', '--password', type="string", help="The password for the user."),
              make_option('-e', '--email', type="string", default=None, help="The email for the user."),
             ])
    def do_register(self, args, opts=None):
        '''Register a username and password combination so you can log in.
        You only need to do this once per user you want to create.
        Calling this more than once with the same arguments will generate
        an error at worst, and be ignored at best.'''
        if not opts:
            username, password, email = args.split(" ")
        else:
            username = opts.username
            password = opts.password
            email = opts.email

        try:
            result = self.client.register(username, password, email)
        except clientlib.RegistrationError as exc:
            self.perror("Error: Registration failed: {0}"
                        .format(exc.message))
            return

        if result:
            self.pfeedback(result)

    @options([make_option('-u', '--username', type="string", default=settings.DEFAULT_USERNAME, help="The user you want to log in as."),
              make_option('-p', '--password', type="string", default=settings.DEFAULT_PASSWORD, help="The password for the user."),
             ])
    def do_login(self, args, opts=None):
        '''Log in as a given user.'''
        if not opts:
            username, password = args.split(' ')
        else:
            username = opts.username
            password = opts.password

        # Sometimes the authserver may not be up.
        if not self.client.ping():
            self.perror("Error: Authentication server is not online.")
            return

        # Let's see if the username and password are right:
        result = self.client.authenticate(username, password)
        if not result:
            self.perror("Authentication failed.")
            return
        else:
            self.pfeedback("Authentication successful. You are now logged in as {0}."
                           .format(repr(username)))

        if args:
            character = self.client.characters[list(self.client.characters)[int(args)]].name
        else:
            character = self.select(self.client.characters, 'Select a Character: ')
        self.client.last_character = character
        self.client.set_character_status(character)

        self.client.get_objects()

        self.format_prompt()

    def do_update(self, args):
        '''Update all the things that can be updated.
        This includes objects only at the moment.'''
        if not self.logged_in():
            return

        self.client.get_objects()
        # TODO: Get messages too.

    def do_map(self, args):
        '''Renders a map of the zone your character is currently in.
        By default this is ascii, but you can also ask it to render to an image.'''
        if not self.logged_in():
            return

        # Get bounds (maxx, maxy, minx, miny) of all objects in the zone
        maxx = 0
        maxy = 0
        minx = 0
        miny = 0
        goodobjs = []
        for objid, obj in self.client.objects.iteritems():
            try:
                objloc = obj['loc']
            except KeyError:
                # Some objects have no location, so skip em.
                continue

            try:
                if 'hidden' in obj['states']:
                    # Skip hidden objects.
                    continue
            except KeyError:
                # Stuff without states are A-OK
                pass

            maxx = max(maxx, objloc['x'])
            maxy = max(maxy, objloc['y'])
            minx = min(minx, objloc['x'])
            miny = min(miny, objloc['y'])
            goodobjs.append(obj)

        xlen, ylen = maxx-minx, maxy-miny

        deltax = maxx-minx
        deltay = maxy-miny

        if not args:
            # Default is fullscreen
            import os
            rows, columns = os.popen('stty size', 'r').read().split()
            mapsizex = int(rows)-2
            mapsizey = int(columns)-1
        else:
            # Otherwise use whatever args are passed.
            mapsizex, mapsizey = [int(n) for n in args.split()]

        import numpy
        # Build out the default array.
        maparray = numpy.array([['.']*mapsizey]*mapsizex)

        # This places the objects in the array based on their relative position.
        names = {}
        for obj in goodobjs:
            # Stupid rounding here, but good enough.
            x = int(((obj['loc']['x']-minx)/deltax)*mapsizex)
            y = int(((obj['loc']['y']-miny)/deltay)*mapsizey)
            try:
                name = names[obj['resource']]
            except KeyError:
                name = obj['resource'][0]
                names[obj['resource']] = name
            maparray[x-1, y-1] = name

        # Make a string because printing manually is dumb.
        mapstring = '\n'.join([''.join([y for y in x]) for x in maparray])
        self.poutput(mapstring)

    def clean_dict(self, dirty):
        newobj = {}
        for k, v in dirty.iteritems():
            if type(v) == float:
                v = float("%.4f" % v)

            if type(v) == dict:
                v = self.clean_dict(v)

            if not k.startswith("_"):
                newobj[k] = v
        return newobj

    def format_object(self, objdata):
        newobj = {u'id': objdata['_id']['$oid']}
        newobj.update(self.clean_dict(objdata))
        for k, v in objdata.iteritems():
            # Prettify the last modified timestamp
            if k == "last_modified":
                v = datetime.fromtimestamp(v[r'$date']/1000.0)\
                            .strftime(settings.DATETIME_FORMAT)
                newobj[k] = v

        return pformat(newobj)

    def get_match(self, objname):
        objname = objname.lower()

        # Try exact match first:
        try:
            obj = self.client.objects[objname]
            return obj
        except KeyError:
            # Couldn't find the exact match.
            pass

        # Try startswith match next:
        for objid, obj in self.client.objects.iteritems():
            if objid.lower().startswith(objname) or obj['name'].lower().startswith(objname):
                return obj

        # Try contains match next:
        for objid, obj in self.client.objects.iteritems():
            if objname in objid.lower() or objname in obj['name'].lower():
                return obj

        # Couldn't find anything.
        return False

    def do_detail(self, args):
        '''Pass in the name or id of the object you want to look at.'''
        objname = args
        if objname:
            obj = self.get_match(objname)

            if obj:
                self.poutput(self.format_object(obj))
            else:
                self.perror("Could not find anything resembling {0}.".format(objname))


if __name__ == "__main__":
    app = InteractiveClient()
    app.cmdloop()
