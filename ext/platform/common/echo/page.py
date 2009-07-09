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
import os
import jsext

class PageController(object):
    def __init__(self, id, module):
        # id assigned to this page by the browser extension
        self.id = id
        # service module that created this instance
        self.module = module
        # observer that receives responses
        self.observer = None
        # if the echo service is started or not for this page
        self.started = False

    def setObserver(self, ob):
        '''
        Store an observer that will get its pushResponse method invoked by
        this instance.
        
        @param ob Object
        '''
        self.observer = ob

    def pushRequest(self, cmd):
        '''
        Invoked by an object when a new request arrives for this page.
        
        @param cmd Dictionary with information about the request
        '''
        if cmd['action'] == 'start-service':
            # start service the echo service for this page
            self._onStart(cmd)
        elif cmd['action'] == 'stop-service':
            # stop the echo service for this page
            self._onStop(cmd)
        elif self.started:
            # handle an echo service command
            self._onRequest(cmd)
        # drop anything else that comes through at this point

    def pushResponse(self, action, **kwargs):
        '''
        Sends a response to the observer.
        
        @param action String name of the action on the response
        @param kwargs Dictionary of keyword arguments to be included in the 
          response
        '''
        cmd = {}
        cmd['action'] = action
        cmd.update(kwargs)
        self.observer.pushResponse(self.id, cmd)

    def _onStart(self, cmd):
        '''
        Handles the start of this service.
        
        @param cmd Dictionary of arguments for service start in the outfox
          protocol
        '''
        if self.started:
            # make sure we haven't already started, if so, send an error
            self.pushResponse('failed-service', 
                description='Service already started.')
        else:
            # send the service started message with the JS extension
            self.pushResponse('started-service', extension=jsext.CLASS)
            self.started = True
        
    def _onStop(self, cmd):
        '''
        Handles the stop of this service.
        
        @param cmd Dictionary of arguments for service stop in the outfox
          protocol
        '''
        if not self.started:
            # make sure we have started, if not, send an error
            self.pushResponse('failed-service', 
                description='Service not started.')
        else:
            # tell the requester that the service is stopped
            self.pushResponse('stopped-service')
            # clean up the observer
            self.observer = None
            self.started = False
        
    def _onRequest(self, cmd):
        '''
        Handles any other request once started.
        
        @param cmd Dictionary of arbitrary command values
        '''
        # find which channel we're attempting to use
        action = cmd.get('action', 'ping')
        if action == 'ping':
            self.pushResponse('pong', text=cmd['text'])
        else:
            self.pushResponse('error', description='Unknown action.')