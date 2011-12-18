
from random import randint

from settings import *

from tornado.web import Application, RequestHandler
from tornado.ioloop import IOLoop

class SimpleHandler(RequestHandler):
    def __init__(self, output, *args):
        self.output = output
        RequestHandler.__init__(self, *args)

    def get(self):
        self.write(self.output)

class BaseHandler(RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")

class BaseServer(Application):
    def __init__(self, handlers):
        '''Expects a list of tuple handlers like:
                [(r"/", MainHandler), (r"/chatsocket", ChatSocketHandler),]
        '''
        settings = {"cookie_secret": [chr(randint(32, 126)) for _ in xrange(75)],
                "login_url": ''.join((PROTOCOL, "://", HOSTNAME, ":", str(AUTHSERVERPORT), "/authenticate")),
                }
        Application.__init__(self, handlers, debug=True, **settings)

    def start(self):
        import tornado.options
        tornado.options.parse_command_line()
        IOLoop.instance().start()
