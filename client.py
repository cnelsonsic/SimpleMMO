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

    @options([make_option('-u', '--username', type="string", help="The name of the user you want to register."),
              make_option('-p', '--password', type="string", help="The password for the user."),
              make_option('-e', '--email', type="string", default=None, help="The email for the user."),
             ])
    def do_register(self, args, opts=None):
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
