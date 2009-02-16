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
FMOD_CHANNEL_FREE = -1
FMOD_DEFAULT = 0x00000000
FMOD_LOOP_NORMAL = 0x00000002
FMOD_2D = 0x00000008
FMOD_HARDWARE = 0x00000020
FMOD_CHANNEL_CALLBACKTYPE_END = 0
FMOD_CHANNEL_CALLBACKTYPE_SYNCPOINT = 2
FMOD_UNICODE = 0x01000000
FMOD_TIMEUNIT_PCM  = 0x00000002

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
        # information about the current speech utterance
        self.utterance = None
        # whether we're playing speech or sound
        self.done_action = None

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
            self.fmod.FMOD_Channel_SetVolume(self.fch, val)

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

    def _onFMODComplete(self):
        # notify about end of stream
        self._notify(self.done_action)
        
        # clean up any previous sound here before handling the next command
        if self.fch:
            snd = c_void_p()
            self.fmod.FMOD_Channel_GetCurrentSound(self.fch, byref(snd))
            self.fmod.FMOD_Sound_Release(snd)
            self.fch = None

        # reset stateful data
        self.utterance = None
        self.busy = False
        self.name = None
        self.done_action = None
        # process the queue
        self._processQueue()

    def _onFMODChannelCallback(self, channel, kind, cmd1, cmd2):
        if kind == FMOD_CHANNEL_CALLBACKTYPE_END:
            self._onFMODComplete()
        elif kind == FMOD_CHANNEL_CALLBACKTYPE_SYNCPOINT:
            self._onFMODSyncPoint(cmd1)
        return FMOD_OK

    def reset(self, cmd):
        ChannelBase.reset(self, cmd)
        # reset any playing channel properties
        if self.fch:
            self._setVolume(self.config['volume'])
            self._setLooping(self.config['loop'])

    def stop(self, cmd):
        # allow base class to clear
        ChannelBase.stop(self, cmd)
        if self.fch:
            # clean up the playing FMOD channel and sound
            snd = c_void_p()
            try:
                # invoking stop immediately calls the callback and doesn't
                # wait for FMOD_System_Update()
                self.fmod.FMOD_Channel_Stop(self.fch)
            except Exception, e:
                pass
    
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
            # use local filename, but decide stream/sound by local flag
            uri = cmd['filename']
        except KeyError:
            try:
                # use remote url, but always stream
                uri = cmd['url']
                local = False
            except KeyError:
                self._notify('error', description='Bad sound URL/filename.')
                return
        # have to encode because FMOD unicode flag doesn't seem to work
        uri = uri.encode('utf-8')
        
        # decide looping or not
        if self.config['loop']:
            flags = FMOD_HARDWARE|FMOD_2D|FMOD_LOOP_NORMAL
        else:
            flags = FMOD_DEFAULT

        if local: 
            # create a sound object, decode entirely in memory for playback
            snd = c_void_p()
            if self.fmod.FMOD_System_CreateSound(self.fsys, uri, flags, 
                None, byref(snd)):
                self._notify('error', description='Bad sound URL/filename.')
                return
        else:
            # create a stream object, stream decoding and playback
            snd = c_void_p()
            if self.fmod.FMOD_System_CreateStream(self.fsys, uri, flags, 
                None, byref(snd)):
                self._notify('error', description='Bad sound URL/filename.')
                return
        
        # set a marker on the first sample so we know when output starts
        pt = c_void_p()
        self.fmod.FMOD_Sound_AddSyncPoint(snd, 0, FMOD_TIMEUNIT_PCM, '', 
            byref(pt))

        # play the sound object, starting paused
        ch = c_void_p()
        if self.fmod.FMOD_System_PlaySound(self.fsys, FMOD_CHANNEL_FREE, snd, True, 
            byref(ch)):
            self._notify('error', description='Bad sound format.')
            self.fmod.FMOD_Sound_Release(snd)
            return

        # set channel volume and callback
        if self.fmod.FMOD_Channel_SetCallback(ch, self.fchcb):
            self._notify('error', description='Cannot set sound callback.')
            self.fmod.FMOD_Sound_Release(snd)
            return
        if self.fmod.FMOD_Channel_SetVolume(ch, c_float(self.config['volume'])):
            self._notify('error', description='Cannot set sound volume.')
            self.fmod.FMOD_Sound_Release(snd)
            return

        # start the sound playing
        if self.fmod.FMOD_Channel_SetPaused(ch, False):
            self._notify('error', description='Cannot start sound.')
            self.fmod.FMOD_Sound_Release(snd)
            return

        # store a reference to the playing channel
        self.fch = ch
        # set flags
        self.name = cmd.get('name')
        self.busy = True
        self.done_action = 'finished-play'
        # notify on start
        self._notify('started-play')

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