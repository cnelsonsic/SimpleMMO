
from random import randint
import subprocess

from settings import *

from tornado.web import Application, RequestHandler
from tornado.ioloop import IOLoop

class BaseHandler(RequestHandler):
    def get_login_url(self):
        return u"/login"

    def get_current_user(self):
        user_json = self.get_secure_cookie("user")
        if user_json:
            return user_json
        else:
            return None

class SimpleHandler(BaseHandler):
    def __init__(self, output, *args):
        self.output = output
        RequestHandler.__init__(self, *args)

    def get(self):
        self.write(self.output)

class BaseServer(Application):
    def __init__(self, handlers):
        '''Expects a list of tuple handlers like:
                [(r"/", MainHandler), (r"/chatsocket", ChatSocketHandler),]
        '''
        settings = {
#                 "cookie_secret": ''.join([chr(randint(32, 126)) for _ in xrange(75)]),
                "cookie_secret": subprocess.check_output('git rev-parse HEAD', shell=True).strip(),
                "login_url": ''.join((PROTOCOL, "://", HOSTNAME, ":", str(AUTHSERVERPORT), "/login")),
                }
        print settings
        Application.__init__(self, handlers, debug=True, **settings)

    def start(self):
        import tornado.options
        tornado.options.parse_command_line()
        IOLoop.instance().start()
