'''
Controller for a single page with multiple audio channels.

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
import os
import jsext

class PageController(object):
    def __init__(self, id, module):
        self.id = id
        self.module = module
        self.channels = {}
        self.observer = None
        self.started = False

    def setObserver(self, ob):
        self.observer = ob

    def pushRequest(self, cmd):
        if cmd['action'] == 'start-service':
            # start service
            self._onStart(cmd)
        elif cmd['action'] == 'stop-service':
            # stop service
            self._onStop(cmd)
        elif self.started:
            # all other requests for channel after started
            self._onChannelCmd(cmd)

    def pushResponse(self, cmd):
        # inform the observer of the response
        self.observer.pushResponse(self.id, cmd)

    def _onStart(self, cmd):
        if self.started:
            # make sure we haven't already started, if so, send an error
            cmd = {}
            cmd['action'] = 'failed-service'
            cmd['description'] = 'service already started'
            self.pushResponse(cmd)
        else:
            # send the service started message with the JS extension
            cmd = {}
            cmd['action'] = 'started-service'
            cmd['extension'] = jsext.CLASS
            self.pushResponse(cmd)
            self.started = True
        
    def _onStop(self,cmd):
        if not self.started:
            # make sure we have started, if not, send an error
            cmd = {}
            cmd['action'] = 'failed-service'
            cmd['description'] = 'service not started'
            self.pushResponse(cmd)
        else:
            # send all services the stop message
            for ch in self.channels.values():
                ch.pushRequest(cmd)
            # tell the requester that the service is stopped
            cmd = {}
            cmd['action'] = 'stopped-service'
            self.pushResponse(cmd)
            # clean up the observer
            self.observer = None
            self.started = False
        
    def _onChannelCmd(self, cmd):
        # find which channel we're attempting to use
        ch_id = cmd.get('channel', 0)
        try:
            # get an existing channel
            ch = self.channels[ch_id]
        except KeyError:
            # build a new channel
            ch = self.module.buildChannel(self.module, ch_id)
            ch.setObserver(self)
            self.channels[ch_id] = ch
        ch.pushRequest(cmd)