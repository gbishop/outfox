'''
pygame channel base class.

Copyright (c) 2008 Carolina Computer Assistive Technology

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
import urllib2
import mp3
from channel import ChannelBase
import pygame.event
import pygame.mixer
import pygame.locals
import weakref
import time

# maximum number of sound channels allowed
MAX_CHANNELS = 256
# mixer sampling rate
MIXER_RATE = 44100
MIXER_BITS = 16
MIXER_CHANNELS = 2

# last event id assigned to a channel
last_id = pygame.locals.USEREVENT+1
# mapping from channel event id to channel object
channel_map = weakref.WeakValueDictionary()
# busy channels
busy_channels = []

def assignIdToChannel(channel):
    global last_id
    id = last_id
    channel_map[id] = channel
    if last_id >= MAX_CHANNELS-1:
        # only allowed 255 unique event numbers
        # @todo: not sure what to do when wrapping to prevent conflicts with 
        # channels still in use...
        last_id = pygame.locals.USEREVENT
    last_id += 1
    return id

def getChannelFromId(id):
    try:
        return channel_map[id]
    except KeyError:
        return None

def setBusyChannel(ch):
    busy_channels.append(ch)

def unsetBusyChannel(ch):
    try:
        busy_channels.remove(ch)
    except ValueError:
        # ignore if channel not busy
        pass

def getBusyChannels():
    return busy_channels

class PygameChannelBase(ChannelBase):
    def __init__(self, ch_id):
        ChannelBase.__init__(self, ch_id)
        # queue of utterance word samples
        self.words = []
        # time of speaking started
        self.start_time = 0
        # channel player
        self.player = None
        # pygame id used to contact this channel for callbacks
        self.player_id = assignIdToChannel(self)
        # whether we're playing speech or sound
        self.done_action = None
        # set config defaults
        self._initializeConfig()
        # initialize engine
        self._initializeEngine()

    def _initializeConfig(self):
        self.config = {}
        self.config['volume'] = 0.9
        self.config['rate'] = 200
        self.config['loop'] = False

    def _initializeEngine(self):
        # init mixer to values that actually work, not what the tts engine
        # dictates
        pygame.mixer.init(MIXER_RATE, -MIXER_BITS, MIXER_CHANNELS)
        # make sure we don't run out of channels easily
        pygame.mixer.set_num_channels(MAX_CHANNELS)

    def shutdown(self, cmd):
        self.stop()
        ChannelBase.shutdown(self, cmd)
    
    def reset(self):
        # reinitialize local config
        self._initializeConfig()
        # reset tts
        self._initializeEngine()

    def stop(self):
        ChannelBase.stop(self)
        self.done_action = None
        self.words = []
        unsetBusyChannel(self)
        if self.player:
            self.player.stop()
            self.player = None
    
    def say(self, cmd):
        # make sure the speech string isn't empty; adhere to protocol
        if not len(cmd['text']):
            return

        # start the common response message
        self.name = cmd.get('name')
        if self.name is not None:
            msg = dict(name=self.name, channel=self.id)
        else:
            msg = dict(channel=self.id)

        # find an open player
        self.player = pygame.mixer.find_channel()
        if self.player is None:
            msg['action'] = 'error'
            msg['description'] = 'No free output channel.'
            self._notify(msg)
            return

        # configure channel volume
        self.player.set_volume(self.config['volume'])
        # configure channel callback
        self.player.set_endevent(self.player_id)

        # synthesize speech
        sound, self.words = self._synthWords(cmd['text'])

        # abort if no sound
        if sound is None:
            return

        # mark the channel as busy for callbacks in the event loop so we can
        # notify observers about word callbacks
        setBusyChannel(self)
        # start playing the sound
        self.start_time = time.time()
        self.player.play(sound)
        # set flags
        self.busy = True
        self.done_action = 'finished-say'

        # notify on start
        msg['action'] = 'started-say'
        self._notify(msg)

    def play(self, cmd):
        # start the common response message
        self.name = cmd.get('name')
        if self.name is not None:
            msg = dict(name=self.name, channel=self.id)
        else:
            msg = dict(channel=self.id)
        
        # check if url is already known to be invalid
        if cmd.get('invalid'):
            msg['action'] = 'error'
            msg['description'] = 'Bad sound URL.'
            msg['url'] = cmd['url']
            self._notify(msg)
            return
            
        # find an open player
        self.player = pygame.mixer.find_channel()
        if self.player is None:
            msg['action'] = 'error'
            msg['description'] = 'No free output channel.'
            self._notify(msg)
            return
        # configure channel volume
        self.player.set_volume(self.config['volume'])
        # configure channel callback
        self.player.set_endevent(self.player_id)

        fn = cmd.get('filename')
        if fn is not None:
            # fetch the file from the local disk
            try:
                fh = file(fn, 'rb')
            except IOError:
                msg['action'] = 'error'
                msg['description'] = 'Bad sound file.'
                msg['filename'] = fn
                self._notify(msg)
                return
            # handle as local where we can seek back to start after trying it
            # as an mp3
            snd = self._soundFromFile(fh)
        else:
            # fetch the file at the url
            try:
                uh = urllib2.urlopen(cmd['url'])
            except urllib2.URLError:
                msg['action'] = 'error'
                msg['description'] = 'Bad sound URL.'
                msg['url'] = cmd['url']
                self._notify(msg)
                return
            # handle as remote where we have to use extension detection because
            # seeking back to start does not work
            snd = self._soundFromURL(uh)
        
        if snd is None:
            msg['action'] = 'error'
            msg['description'] = 'Bad sound format.'
            msg['url'] = cmd['url']
            # bad sound format, abort
            self._notify(msg)
            return

        # configure looping
        if self.config['loop']:
            loops = -1
        else:
            loops = 0
        self.player.play(snd, loops)
        # set flags
        self.name = cmd.get('name')
        self.busy = True
        self.done_action = 'finished-play'

        # notify on start
        msg['action'] = 'started-play'
        self._notify(msg)

    def _soundFromFile(self, handle):
        # we can reset a local file stream, so first try as mp3
        try:
            return mp3.MakeSound(handle)
        except Exception, e:
            # seek back to the file start
            handle.seek(0)
        # now try as whatever pygame can support
        try:
            # @todo: does this work in pygame 1.7.1?
            snd = pygame.mixer.Sound(handle)
        except pygame.error:
            snd = None
        return snd

    def _soundFromURL(self, handle):
        # we can't seek backward after reading data from the url stream so we
        # have to check for mp3 at the end of the url as signifying the file
        # type and how to handle it
        if handle.url.endswith('mp3'):
            try:
                # might be an mp3, try to decode
                snd = mp3.MakeSound(handle)
            except Exception, e:
                snd = None
        else:
            try:
                # @todo: does this work in pygame 1.7.1?
                snd = pygame.mixer.Sound(handle)
            except pygame.error:
                snd = None
        return snd

    def getConfig(self, cmd):
        # add all voice names to config
        cfg = dict(voices=self._getVoices())
        cfg.update(self.config)
        self._notify({'action' : 'set-config',
                                 'channel' : self.id,
                                 'config' : cfg})

    def setProperty(self, cmd):
        name = cmd['name']
        val = cmd['value']
        if name == 'rate':
            self._setSpeechRate(val)
        elif name == 'volume':
            if self.player is not None:
                self.player.set_volume(val)
        elif name == 'voice':
            self._setSpeechVoice(val)
        elif name == 'loop':
            # nothing to do; loop is a param on play call
            pass
        else:
            return
        # store in config so we can refer to it later
        self.config[name] = val
        # notify observer
        self._notify({'channel' : self.id, 
                      'action' : 'set-property',
                      'name' : name,
                      'value' : val})

    def onBusyTick(self):
        while len(self.words):
            # peek at the first word metadata
            word = self.words[0]
            # compute samples traversed since start
            curr_sample = (time.time() - self.start_time) * MIXER_RATE
            # compare to current word sample number
            if curr_sample >= word[2]:
                # ignore bogus words
                if word[1] > 0:
                    # notify observer about word start
                    msg = {'channel' : self.id, 'action' : 'started-word',
                           'location' : word[0], 'length' : word[1]}
                    if self.name is not None:
                        msg['name'] = self.name
                    self._notify(msg)
                # pop the word
                self.words.pop(0)
            else:
                # quit
                break

    def onPlayerComplete(self):
        # see if there are any word notifications left
        for word in self.words:
            # ignore bogus words
            if word[1] == 0: continue
            # notify observer about word start
            msg = {'channel' : self.id, 'action' : 'started-word',
                   'location' : word[0], 'length' : word[1]}
            if self.name is not None:
                msg['name'] = self.name
            self._notify(msg)
    
        # throw away our player reference
        self.player = None

        # notify about end of stream
        msg = {'channel' : self.id, 'action' : self.done_action}
        if self.name is not None:
            msg['name'] = self.name
        self._notify(msg)

        # reset stateful data
        self.words = []
        unsetBusyChannel(self)
        self.busy = False
        self.name = None
        self.done_action = None
        # process the queue
        self._processQueue()
