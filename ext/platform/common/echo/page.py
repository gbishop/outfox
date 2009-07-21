'''
Controller for a single page using the echo service.

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
import os
import jsext

class PageController(PageController):
    def onStart(self, cmd):
        '''
        Handles an echo service start request.
        
        @param cmd Dictionary of arguments for service start in the outfox
          protocol
        @return JS methods to add to the outfox.<service name> object if the 
          service is ready for use, or None if the the subclass will send the
          service started response at a later point
        '''
        return jsext.CLASS

    def onRequest(self, cmd):
        '''
        Handles an echo service ping request.
        
        @param cmd Dictionary of arbitrary command values
        '''
        # find which channel we're attempting to use
        action = cmd.get('action', 'ping')
        if action == 'ping':
            self.pushResponse('pong', text=cmd['text'])
        else:
            self.pushResponse('error', description='Unknown action.')