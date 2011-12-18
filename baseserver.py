
from tornado.web import Application, RequestHandler
from tornado.ioloop import IOLoop

class SimpleHandler(RequestHandler):
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
        Application.__init__(self, handlers, debug=True)

    def start(self):
        import tornado.options
        tornado.options.parse_command_line()
        IOLoop.instance().start()
