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
from ..page import PageController
from channel import ChannelBase
import os
import jsext

class PageController(PageController):
    def __init__(self, id, module):
        super(PageController, self).__init__(id, module)
        self.channels = {}

    def onStart(self, cmd):
        '''
        Handles an audio service start request.
        
        @param cmd Dictionary of arguments for service start in the outfox
          protocol
        @return JS methods to add to the outfox.<service name> object if the 
          service is ready for use, or None if the the subclass will send the
          service started response at a later point
        '''
        return jsext.CLASS

    def onStop(self,cmd):
        '''
        Handles an audio service stop request.
        
        @param cmd Dictionary of arguments for service stop in the outfox
          protocol
        '''
        # send all channels the stop message
        for ch in self.channels.values():
            try:
                ch.pushRequest(cmd)
            except Exception, e:
                # ignore any errors during shutdown
                pass
        
    def onRequest(self, cmd):
        '''
        Dispatches all other requests to channel controllers.
        
        @param cmd Dictionary of arbitrary command values
        '''
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
            self.pushResponse('error', description=str(e), channel=ch.id)
            ChannelBase.processNext(ch, '_processQueue')