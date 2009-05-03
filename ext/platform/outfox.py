#!/usr/bin/env python
'''
Main controller for the speech servers.

Copyright (c) 2008, 2009 Carolina Computer Assistive Technology

Permission to use, copy, modify, and distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
'''
import simplejson
import socket
import sys

DELIMITER = '\3'

class Outfox(object):
    def __init__(self, port, service):
        # map page IDs to page controllers
        self.pages = {}
        self.port = port
        self.service = service
        self.module = None
        self.server = None

    def run(self):
        # locate the proper module for this platform
        self.module = self._findModule()
        if self.module is None:
            msg = 'Service not supported on this platform'
            self._notify('*', action='failed-service', description=msg)
            raise NotImplementedError(msg)

        # launch the socket server
        self.server = self.module.buildServer(self.module, self.port)
        # observe socket server messages so we can dispatch
        self.server.setObserver(self)
        # let the server connect
        self.server.doConnect()

        # let the module dictate what happens next
        self.module.run(self.module)
        
    def _notify(self, page_id, cmd=None, **kwargs):
        if cmd is None:
            cmd = {}
            cmd.update(kwargs)
        cmd['service'] = self.service
        json = simplejson.dumps({'page_id' : page_id, 'cmd' : cmd})
        if self.server:
            # use the json server
            self.server.sendMessage(json+DELIMITER)            
        else:
            # open a new socket to report the failure
            s = socket.socket()
            s.connect(('127.0.0.1', self.port))
            s.sendall(json+DELIMITER)            

    def shutdown(self):
        self.module.shutdown(self.module)

    def pushRequest(self, json):
        try:
            # decode the json
            dec = simplejson.loads(json)
            page_id = dec['page_id']
        except Exception:
            # just ignore bad json or missing page IDs; don't know what page
            # sent it
            return

        try:
            # get the command
            cmd = dec['cmd']
        except KeyError:
            # notify about missing commands
            self._notify(page_id, action='error', 
                description='Missing command payload.')
            return

        try:
            # get the page matching the given id
            page = self.pages[page_id]
        except KeyError:
            # build a new page and register as a observer
            page = self.module.buildPage(self.module, page_id)
            page.setObserver(self)
            self.pages[page_id] = page
            
        try:
            # let the page controller dispatch the message
            page.pushRequest(cmd)
        except Exception, e:
            # if the service did not handle the error, something really bad
            # happened so best that we notify that the entire service failed
            self._notify('*', action='failed-service', description=str(e))
            return

        # remove page reference if destroying, even if we just created
        if cmd.get('action') == 'stop-service':
            del self.pages[page_id]

    def pushResponse(self, page_id, cmd):
        # add service name to the command
        cmd['service'] = self.service
        # encode as json
        msg = simplejson.dumps({'page_id' : page_id, 'cmd' : cmd})
        # send using the server
        self.server.sendMessage(msg)

    def _findModule(self):
        if sys.platform == 'darwin':
            pkg = 'osx'
        elif sys.platform == 'win32':
            pkg = 'win32'
        else:
            pkg = 'nix'
        module = None
        try:
            name = '%s.%s' % (pkg, self.service)
            module = __import__(name, globals(), locals(), [self.service])
        except Exception, e:
            print 'import failed', e
        return module

def main():
    import sys
    pid = os.getpid()
    if sys.platform == 'win32':
        sys.stderr = sys.stdout = file('c:\\outfox.log', 'w')
    print 'Launching Outfox:', pid
    # not possible to tell the launcher that the port number is missing, so just
    # fail with an exception
    port = int(sys.argv[1])
    service = sys.argv[2]
    # create the main controller
    fs = Outfox(port, service)
    fs.run()
    print 'Quitting Outfox:', pid

if __name__ == "__main__":
    import os
    main()
