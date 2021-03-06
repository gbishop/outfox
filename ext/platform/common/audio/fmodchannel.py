'''
FMOD channel base class.

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
from ctypes import *
from utterance import Utterance
from channel import ChannelBase

FMOD_OK = 0
FMOD_ERR_NOTREADY = 55
FMOD_OPENSTATE_READY = 0
FMOD_OPENSTATE_ERROR = 2
FMOD_CHANNEL_FREE = -1
FMOD_DEFAULT = 0x00000000
FMOD_LOOP_OFF = 0x00000001
FMOD_LOOP_NORMAL = 0x00000002
FMOD_2D = 0x00000008
FMOD_HARDWARE = 0x00000020
FMOD_SOFTWARE = 0x00000040
FMOD_NONBLOCKING = 0x00010000
FMOD_CHANNEL_CALLBACKTYPE_END = 0
FMOD_CHANNEL_CALLBACKTYPE_SYNCPOINT = 2
FMOD_UNICODE = 0x01000000
FMOD_TIMEUNIT_PCM  = 0x00000002

class FMOD_CREATESOUNDEXINFO(Structure):
    _fields_ = [
        ('cbsize', c_int),
        ('length', c_uint),
        ('fileoffset', c_uint),
        ('numchannels', c_int),
        ('defaultfrequency', c_int),
        ('format', c_uint),
        ('decodebuffersize', c_uint),
        ('initialsubsound', c_int),
        ('numsubsounds', c_int),
        ('inclusionlist', POINTER(c_int)),
        ('inclusionlistnum', c_int),
        ('pcmreadcallback', c_void_p),
        ('pcmsetposcallback', c_void_p),
        ('nonblockcallback', CFUNCTYPE(c_void_p, c_void_p, c_int)),
        ('dlsname', c_char_p),
        ('encryptionkey', c_char_p),
        ('maxpolyphony', c_int),
        ('userdata', c_void_p),
        ('suggestedsoundtype', c_uint),
        ('useropen', c_void_p),
        ('userclose', c_void_p),
        ('userread', c_void_p),    
        ('userseek', c_void_p),
        ('speakermap', c_uint),
        ('initialsoundgroup', c_void_p),
        ('initialseekposition', c_uint),
        ('initialseekpostype', c_uint)
    ]

class FMODChannelBase(ChannelBase):
    '''
    @ivar fmod FMOD module
    @ivar fsys FMOD system object
    @ivar fch FMOD channel object
    @ivar fchcb FMOD channel callback
    @ivar utterance Object containing speech utterance information
    @ivar done_action String indicating if current playback is speech or sound
    @ivar config Dictionary of name/value configuration pairs
    '''
    def __init__(self, ch_id, fmod, fsys):
        # initialize base class
        ChannelBase.__init__(self, ch_id)
        # store fmod library
        self.fmod = fmod
        # store fmod system object
        self.fsys = fsys
        # no playing channel to start
        self.fch = None
        # create channel callback
        cb_factory = CFUNCTYPE(c_int, c_void_p, c_int, c_int, c_int)
        self.fchcb = cb_factory(self._onFMODChannelCallback)
        # create non-block callback
        #cb_factory = CFUNCTYPE(c_void_p, c_void_p, c_int)
        #self.nbcb = cb_factory(self._onFMODNonBlockingCallback)
        # information about the current speech utterance
        self.utterance = None
        # whether we're playing speech or sound
        self.done_action = None
        # in memory cache of small sounds that ff did not cache on disk
        self.sound_cache = {}
        # whether we're playing a cached sound or not
        self.done_cached = False

    def _synthesizeUtterance(self, text):
        '''
        Override to synthesize speech for the given text.

        @param text String of text to speak
        @return Utterance instance
        '''
        return Utterance(text)

    def _outputUtterance(self, utterance):
        '''
        Override to control how the synthesized speech utterance is output.

        @param utterance Utterance instance
        @return True on success or False on failure
        '''
        return False

    def _getVoices(self):
        '''
        Override to provide a list of all available voices.

        @return Array of voice names as strings
        '''
        pass

    def _setRate(self, val):
        '''
        Override to set the speech rate of the channel immediately.

        @param val Integer rate in words per minute
        '''
        pass
        
    def _setVolume(self, val):
        '''
        Override to set the volume of the channel immediately.

        @param val Integer rate in words per minute
        '''
        if self.fch is not None:
            self.fmod.FMOD_Channel_SetVolume(self.fch, c_float(val))

    def _setVoice(self, val):
        '''
        Override to set the voice of the channel immediately.

        @param val String name of the voice
        '''
        pass
        
    def _setLooping(self, val):
        '''
        Override to set the looping property of the channel immediately.
        
        @param val Boolean looping flag
        '''
        if self.done_action != 'finished-say' and self.fch is not None:
            count = -1 if val else 0
            self.fmod.FMOD_Channel_SetLoopCount(self.fch, count)

    def _onFMODSyncPoint(self, index):
        '''
        Override to handle synchronization points in sounds.

        @param index Integer sample offset of the sync point
        '''
        if index == 0:
            # notify on output start
            self._notify('started-output')
            
    def _resetFlags(self):
        self.snd = None
        self.utterance = None
        self.busy = False
        self.name = None
        self.done_action = None
        self.done_cached = False        

    def _onFMODComplete(self):
        # notify about end of stream
        self._notify(self.done_action)
        
        # clean up any previous sound here before handling the next command
        if self.fch and not self.done_cached:
            snd = c_void_p()
            self.fmod.FMOD_Channel_GetCurrentSound(self.fch, byref(snd))
            self.fmod.FMOD_Sound_Release(snd)
        self.fch = None

        # reset stateful data
        self._resetFlags()
        # mark this channel ready for processing
        ChannelBase.processNext(self, '_processQueue')

    def _onFMODChannelCallback(self, channel, kind, cmd1, cmd2):
        if kind == FMOD_CHANNEL_CALLBACKTYPE_END:
            self._onFMODComplete()
        elif kind == FMOD_CHANNEL_CALLBACKTYPE_SYNCPOINT:
            self._onFMODSyncPoint(cmd1)
        return FMOD_OK

    def _onFMODNonBlockingCallback(self, snd):
        # make sure this channel is still busy trying to load the sound and 
        # hasn't been stopped; if it has, free the sound and let the main loop
        # continue
        if self.snd is not snd:
            self.fmod.FMOD_Sound_Release(snd)
            return

        # make sure the async sound is ready for further use before performing
        # any actions on it; if it isn't 
        state = c_int()
        rv = self.fmod.FMOD_Sound_GetOpenState(snd, byref(state), None, None)
        if state.value == FMOD_OPENSTATE_ERROR:
            # sound error; stop trying to handle this sound
            self._notify('error', description='Cannot load sound data.')
            self.fmod.FMOD_Sound_Release(snd)
            self._resetFlags()
            ChannelBase.processNext(self, '_processQueue')
            return
        elif state.value != FMOD_OPENSTATE_READY:
            # not ready for sound to start yet; try again later with the same
            # parameters
            ChannelBase.processNext(self, '_onFMODNonBlockingCallback', snd)
            return

        self._execFMODAudio(snd)
        
    def _buildFMODAudio(self, cmd, local):
        # default to not caching sound in memory
        self.done_cached = False
        try:
            # use local filename, but decide stream/sound by local flag
            uri = cmd['filename']
        except KeyError:
            try:
                # use remote url
                uri = cmd['url']
            except KeyError:
                self._notify('error', description='Bad sound URL/filename.')
                return
            if cmd['cache'] == True:
                # treat as a sound and store it in the memory cache
                local = True
                self.done_cached = True
            else:
                # treat as a stream and never cache
                local = False
        # have to encode because FMOD unicode flag doesn't seem to work
        uri = uri.encode('utf-8')
        
        # always allow for looping
        flags = FMOD_SOFTWARE|FMOD_2D|FMOD_LOOP_NORMAL

        # open blocking if opening from local cache, else open nonblocking
        if not self.done_cached:
            flags |= FMOD_NONBLOCKING

        if local:
            # create a sound object, decode entirely in memory for playback
            snd = c_void_p()
            if self.fmod.FMOD_System_CreateSound(self.fsys, uri, flags, 
                None, byref(snd)):
                self._notify('error', description='Bad sound URL/filename.')
                return None
        else:
            # create a stream object, chunk decoding and playback
            snd = c_void_p()
            if self.fmod.FMOD_System_CreateStream(self.fsys, uri, flags, 
                None, byref(snd)):
                self._notify('error', description='Bad sound URL/filename.')
                return None
        
        if self.done_cached:
            # cache sound in memory if it's small
            self.sound_cache[uri] = snd

        return snd
        
    def _execFMODAudio(self, snd):
        # set a marker on the first sample so we know when output starts
        pt = c_void_p()
        rv = self.fmod.FMOD_Sound_AddSyncPoint(snd, 0, FMOD_TIMEUNIT_PCM, '', 
            byref(pt))
        if rv:
            self._notify('error', description='Cannot set sound start marker.')
            self.fmod.FMOD_Sound_Release(snd)
            self._resetFlags()
            ChannelBase.processNext(self, '_processQueue')
            return rv
        
        # play the sound object, starting paused
        ch = c_void_p()
        rv = self.fmod.FMOD_System_PlaySound(self.fsys, FMOD_CHANNEL_FREE, snd,
            True, byref(ch))
        if rv:
            self._notify('error', description='Bad sound format.')
            self.fmod.FMOD_Sound_Release(snd)
            self._resetFlags()
            ChannelBase.processNext(self, '_processQueue')
            return rv

        # set channel volume and callback
        rv = self.fmod.FMOD_Channel_SetCallback(ch, self.fchcb)
        if rv:
            self._notify('error', description='Cannot set sound callback.')
            self.fmod.FMOD_Sound_Release(snd)
            self._resetFlags()
            ChannelBase.processNext(self, '_processQueue')
            return rv
        rv = self.fmod.FMOD_Channel_SetVolume(ch, c_float(self.config['volume']))
        if rv:
            self._notify('error', description='Cannot set sound volume.')
            self.fmod.FMOD_Sound_Release(snd)
            self._resetFlags()
            ChannelBase.processNext(self, '_processQueue')
            return rv
        count = -1 if self.config['loop'] else 0
        rv = self.fmod.FMOD_Channel_SetLoopCount(ch, count)
        if rv:
            self._notify('error', description='Cannot set looping.')
            self.fmod.FMOD_Sound_Release(snd)
            self._resetFlags()
            ChannelBase.processNext(self, '_processQueue')
            return rv

        # start the sound playing
        rv = self.fmod.FMOD_Channel_SetPaused(ch, False)
        if rv:
            self._notify('error', description='Cannot start sound.')
            self.fmod.FMOD_Sound_Release(snd)
            self._resetFlags()
            ChannelBase.processNext(self, '_processQueue')
            return rv

        # store a reference to the playing channel
        self.fch = ch

    def reset(self, cmd):
        ChannelBase.reset(self, cmd)
        # reset any playing channel properties
        if self.fch:
            self._setVolume(self.config['volume'])
            self._setLooping(self.config['loop'])
            # free up sounds in the memory cache
            [self.fmod.FMOD_Sound_Release(snd) 
                for snd in self.sound_cache.values()]
            self.sound_cache = {}

    def stop(self, cmd):
        # allow base class to clear
        ChannelBase.stop(self, cmd)
        if self.fch:
            # clean up the playing FMOD channel and sound
            snd = c_void_p()
            try:
                # immediately invokes the calback on *nux, but no where else?
                # yuck!
                self.fmod.FMOD_Channel_Stop(self.fch)
            except Exception, e:
                pass
        else:
            self._onFMODComplete()
    
    def say(self, cmd):
        # make sure the speech string isn't empty; adhere to protocol of noop
        if not len(cmd['text']):
            return

        # synthesize utterance
        utter = self._synthesizeUtterance(cmd['text'])
        # output utterance
        if not self._outputUtterance(utter):
            return
        # store utterace data
        self.utterance = utter
        
        # set flags
        self.name = cmd.get('name')
        self.busy = True
        self.done_action = 'finished-say'
        # notify on start
        self._notify('started-say')

    def play(self, cmd, local):
        # check if url is already known to be invalid
        if cmd.get('invalid'):
            self._notify('error', description='Bad sound URL.', url=cmd['url'])
            return
        
        try:
            # try to fetch a sound from the in-memory cache
            snd = self.sound_cache[cmd['url'].encode('utf-8')]
            self.done_cached = True
        except KeyError:
            # build a new sound or stream, set done_cached also
            snd = self._buildFMODAudio(cmd, local)
            # leave if sound was not created; method already notified client
            if snd is None: return

        # set flags
        self.name = cmd.get('name')
        self.busy = True
        self.done_action = 'finished-play'
        # notify on start
        self._notify('started-play')
        
        if self.done_cached:
            # if caching, opened blocking so start immediately
            self._execFMODAudio(snd)
        else:
            # if non-blocking, handle on next main loop iteration
            ChannelBase.processNext(self, '_onFMODNonBlockingCallback', snd)
        # store the sound for later comparison
        self.snd = snd

    def getConfig(self, cmd):
        # add all voice names to config
        cfg = dict(voices=self._getVoices())
        cfg.update(self.config)
        self._notify('set-config', config=cfg)

    def setProperty(self, cmd):
        name = cmd['name']
        val = cmd['value']
        if name == 'rate':
            self._setRate(val)
        elif name == 'volume':
            self._setVolume(val)
        elif name == 'voice':
            self._setVoice(val)
        elif name == 'loop':
            self._setLooping(val)
        else:
            return
        # store in config so we can refer to it later
        self.config[name] = val
        # notify observer
        self._notify('set-property', name=name, value=val)