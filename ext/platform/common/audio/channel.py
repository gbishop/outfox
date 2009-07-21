'''
Abstract base class for audio speech and sound command processing. Provides
methods shared among all platform implementations.

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

class ChannelBase(object):
    '''
    @cvar toProcess List of channels that need queue processing
    @ivar id Integer channel ID assigned by client
    @ivar observer Object observing channel responses
    @ivar queue Array queue of commands to process
    @ivar deferred Array of deferred commands to hold
    @ivar stalled_id Integer deferred ID that stalled the queue last
    @ivar busy Boolean busy flag for this channel
    @ivar name String name of the last command to include in all responses
    '''
    toProcess = []
    def __init__(self, ch_id):
        # unique id for this channel
        self.id = ch_id
        # observer for channel callbacks
        self.observer = None
        # queue of utterances
        self.queue = []
        # deferred results
        self.deferreds = {}
        # latest deferred request id that stalled the queue
        self.stalled_id = None
        # busy flag; used instead of tts and sound busy methods which are
        # not documented as to when they are set and reset
        self.busy = False
        # name assigned by the client to a speech utterance or sound that
        # can be paired with callback data
        self.name = None
        # set config defaults
        self._initializeConfig()
        
    @classmethod
    def processNext(cls, ch, mtd, *args, **kwargs):
        cls.toProcess.append((ch, mtd, args, kwargs))
        
    @classmethod
    def processPending(cls):
        [getattr(ch, mtd)(*args, **kwargs) 
            for ch, mtd, args, kwargs in cls.toProcess]
        cls.toProcess = []

    def _processQueue(self):
        while (not self.busy) and len(self.queue):
            # peek at the top command to see if it is deferred
            cmd = self.queue[0]
            reqid = cmd.get('deferred')
            if reqid is not None:
                # check if the deferred result is already available
                result = self.deferreds.get(reqid)
                if result is None:
                    # store the current request ID
                    self.stalled_id = reqid
                    # and stall the queue for now
                    return
                else:
                    # set the deferred result action to that of the original
                    result['action'] = cmd['action']
                    # remove the deferred from the list of deferreds
                    del self.deferreds[reqid]
                    # use the result instead of the original
                    cmd = result
            # remember to pop the command
            cmd = self.queue.pop(0)
            # handle the next command
            self._handleCommand(cmd)   

    def _notify(self, action, **kwargs):
        msg = {}
        msg['channel'] = self.id
        if self.name is not None:
            msg['name'] = self.name
        msg.update(kwargs)
        if self.observer is not None:
            self.observer.pushResponse(action, **msg)

    def _handleCommand(self, cmd):
        action = cmd.get('action')
        if action == 'say':
            self.say(cmd)
        elif action == 'play':
            self.play(cmd, True)
        elif action == 'stream':
            self.play(cmd, False)
        elif action == 'set-queued':
            self.setProperty(cmd)
        elif action == 'get-config':
            self.getConfig(cmd)
        elif action == 'reset-queued':
            self.reset(cmd)

    def setObserver(self, ob):
        self.observer = ob

    def pushRequest(self, cmd):
        action = cmd.get('action')
        if action == 'stop':
            # process stops immediately
            self.stop(cmd)
        elif action == 'set-now':
            # process immediate property changes
            self.setProperty(cmd)
        elif action == 'reset-now':
            # process immediate reset of all properties
            self.reset(cmd)
        elif action == 'deferred-result':
            # process incoming deferred result
            self.deferred(cmd)
        elif action == 'stop-service':
            # shutdown this channel
            self.shutdown(cmd)
        else:
            # queue command; slight waste of time if we immediately pull it back
            # out again, but it's clean
            self.queue.append(cmd)
            # process the queue
            self._processQueue()
            
    def _initializeConfig(self):
        '''Override to change the default channel configuration.'''
        self.config = {}
        self.config['volume'] = 0.9
        self.config['rate'] = 200
        self.config['loop'] = False
        
    def say(self, cmd):
        '''Override to process a say command.'''
        pass
        
    def play(self, cmd):
        '''Override to process a play command.'''
        pass
        
    def setProperty(self, cmd):
        '''Override to process a property change command.'''        
        pass
        
    def getConfig(self, cmd):
        '''Override to process the initial configuration request command.'''
        pass
        
    def reset(self, cmd):
        '''Override to process a reset command for this channel.'''
        self._initializeConfig()

    def deferred(self, cmd):
        '''Override to process the result of a deferred command.'''
        try:
            reqid = cmd['deferred']
        except KeyError:
            return
        # put the deferred into holding
        self.deferreds[reqid] = cmd
        # check if this deferred is the one that stalled the pipe
        if reqid == self.stalled_id:
            # if so, pump the queue
            self._processQueue()
        # if not, just continue

    def stop(self, cmd):
        '''Override to process a stop command.'''
        # reset queue
        self.queue = []
        # reset deferreds
        self.stalled_id = None
        self.deferreds = {}
        # don't reset name and busy in case next callback needs them
        
    def shutdown(self, cmd):
        '''Override to process a handle shutdown command.'''
        self.stop(cmd)
        self.observer = None
