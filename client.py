from cmd2 import Cmd, options, make_option
import logging
logging.basicConfig()
# We don't care about clientlib logging.
logging.getLogger('clientlib').setLevel(logging.CRITICAL)
import clientlib

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

    @options([make_option('-u', '--username', type="string", help="The user you want to log in as."),
              make_option('-p', '--password', type="string", help="The password for the user."),
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

        self.prompt = "{0} > ".format(username)


if __name__ == "__main__":
    app = InteractiveClient()
    app.cmdloop()
