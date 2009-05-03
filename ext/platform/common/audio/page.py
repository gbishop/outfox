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
from channel import ChannelBase
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
        
    def _notify(self, action, **kwargs):
        cmd = {}
        cmd['action'] = action
        cmd.update(kwargs)
        self.observer.pushResponse(self.id, cmd)

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
            self._notify('failed-service', 
                description='Service already started.')
        else:
            # send the service started message with the JS extension
            self._notify('started-service', extension=jsext.CLASS)
            self.started = True
        
    def _onStop(self,cmd):
        if not self.started:
            # make sure we have started, if not, send an error
            self._notify('failed-service', description='Service not started.')
        else:
            # send all channels the stop message
            for ch in self.channels.values():
                try:
                    ch.pushRequest(cmd)
                except Exception, e:
                    # ignore any errors during shutdown
                    pass
            # tell the requester that the service is stopped
            self._notify('stopped-service')
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
            
        try:
            # give the command to the channel to handle
            ch.pushRequest(cmd)
        except Exception, e:
            # if the channel raises an exception, notify the client of an error
            # also, mark the channel as needing processing on the next run loop
            # iteration so it doesn't stall indefinitely
            self._notify('error', description=str(e), channel=ch.id)
            ChannelBase.processNext(ch, '_processQueue')