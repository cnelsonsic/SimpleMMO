
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

import settings
import logging
logging.getLogger('requests.packages.urllib3.connectionpool').setLevel(logging.WARN)

from tornado.web import Application, RequestHandler
from tornado.ioloop import IOLoop

client = False
try:
    if settings.SENTRY:
        from raven import Client

        import requests
        try:
            r = requests.get(settings.SENTRY_SERVER)
            sentry_up = 'Sentry' in r.content
        except requests.ConnectionError:
            sentry_up = False

        if sentry_up:
            client = Client(settings.SENTRY_DSN)
            if settings.SENTRY_LOG:
                from raven.handlers.logging import SentryHandler
                from raven.conf import setup_logging
                handler = SentryHandler(client)
                setup_logging(handler)

except ImportError:
    print "Set up Sentry for consolidated logging and error reporting!"


class BaseHandler(RequestHandler):
    def _handle_request_exception(self, e):
        if client:
            client.captureException()
        RequestHandler._handle_request_exception(self, e)

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


from subprocess import Popen, PIPE
def get_gitsha():
    return Popen("git rev-parse --short HEAD", shell=True, stdout=PIPE).communicate()[0].strip()
def get_commits():
    return Popen("git rev-list --all | wc -l", shell=True, stdout=PIPE).communicate()[0].strip()

class VersionHandler(BaseHandler):
    def get(self):
        gitsha = get_gitsha()
        commits = get_commits()
        self.write('\n'.join((gitsha, commits)))

class SelfServe(BaseHandler):
    '''Provides a method to comply with AGPL licensing.
    This allows a request handler to respond to something like "/source"
    and iterate through the local directory, adding files it finds with an
    AGPL license to a zipfile and returning that when it is done.
    It skips any directories that contain any of the strings in settings.SKIP_FOLDERS.
    '''

    def get(self):
        from zipfile import ZipFile
        import os
        import uuid
        # Get all files in this folder and all folders below it.
        outfile = "/tmp/%s.zip" % str(uuid.uuid4())
        z = ZipFile(outfile, "w")
        for root, dirs, files in os.walk("."):
            skip = False
            for no in settings.SKIP_FOLDERS:
                if no in root:
                    skip = True
                    break
            if skip:
                continue

            for filename in files:
                # Search them all for "BEGIN AGPL LICENSE BLOCK"
                print "Searching %s" % os.path.join(root, filename)
                if settings.AGPL_STRING in open(os.path.join(root, filename), "r").read():
                    print "Added %s to archive." % filename
                    z.write(os.path.join(root, filename))
        z.close()
        # Zip all those up and return it.
        self.set_header('content-type', 'application/zip')
        self.set_header('content-disposition', "attachment;filename=SimpleMMO_%s-%s.zip" % (get_commits(), get_gitsha()))
        with open(outfile, "r") as f:
            archive = f.read()
        # Delete outfile.
        self.write(archive)

class BaseServer(Application):
    def __init__(self, extra_handlers):
        '''Expects a list of tuple handlers like:
                [(r"/", MainHandler), (r"/chatsocket", ChatSocketHandler),]
        '''
        url = settings._server_str % (settings.PROTOCOL, settings.HOSTNAME, settings.AUTHSERVERPORT)

        app_settings = {
                "cookie_secret": settings.COOKIE_SECRET,
                "login_url": ''.join((url, "/login")),
                }

        handlers = []
        handlers.append((r"/version", VersionHandler))
        handlers.append((r"/source", SelfServe))

        handlers.extend(extra_handlers)

        Application.__init__(self, handlers, debug=True, **app_settings)

    def start(self):
        import tornado.options
        tornado.options.parse_command_line()
        IOLoop.instance().start()
