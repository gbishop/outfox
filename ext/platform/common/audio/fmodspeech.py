'''
FMOD speech base class supporing 8 and 16 bit speech samples.

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
from fmodchannel import FMODChannelBase, FMOD_CREATESOUNDEXINFO

FMOD_CHANNEL_FREE = -1
FMOD_SOUND_FORMAT_PCM8 = 1
FMOD_SOUND_FORMAT_PCM16 = 2
FMOD_OPENMEMORY = 0x00000800
FMOD_OPENRAW = 0x00001000
FMOD_TIMEUNIT_PCM  = 0x00000002

class FMODSpeechBase(FMODChannelBase):
    def _outputUtterance(self, utterance):
        # do nothing if there are no samples
        if len(utterance.samples) == 0:
            return False
            
        # pointer to samples
        buff = c_char_p(utterance.samples)
        # create sound info struct
        info = FMOD_CREATESOUNDEXINFO()
        info.cbsize = sizeof(info)
        info.length = len(utterance.samples)
        info.numchannels = utterance.channels
        info.defaultfrequency = utterance.rate
        if utterance.depth == 8:
            info.format = FMOD_SOUND_FORMAT_PCM8
        elif utterance.depth == 16:
            info.format = FMOD_SOUND_FORMAT_PCM16
        
        # create a sound object
        snd = c_void_p()
        flags = FMOD_OPENRAW | FMOD_OPENMEMORY
        if self.fmod.FMOD_System_CreateSound(self.fsys, buff, flags, 
            byref(info), byref(snd)):
            self._notify('error', description='Bad speech buffer.')
            return False
            
        # set a marker on the first sample so we know when output starts
        pt = c_void_p()
        self.fmod.FMOD_Sound_AddSyncPoint(snd, 0, FMOD_TIMEUNIT_PCM, '', 
            byref(pt))
            
        # set word markers on the sound
        for word in utterance.words:
            self.fmod.FMOD_Sound_AddSyncPoint(snd, word[2], FMOD_TIMEUNIT_PCM, 
                '', byref(pt))

        # play the sound object, starting paused
        ch = c_void_p()
        if self.fmod.FMOD_System_PlaySound(self.fsys, FMOD_CHANNEL_FREE, snd, True, 
            byref(ch)):
            self._notify('error', description='Bad speech format.')
            self.fmod.FMOD_Sound_Release(snd)
            return False

        # set channel volume, callback, loop
        if self.fmod.FMOD_Channel_SetCallback(ch, self.fchcb):
            self._notify('error', description='Cannot set speech callback.')
            self.fmod.FMOD_Sound_Release(snd)
            return False
        if self.fmod.FMOD_Channel_SetVolume(ch, c_float(self.config['volume'])):
            self._notify('error', description='Cannot set speech volume.')
            self.fmod.FMOD_Sound_Release(snd)
            return False
        if self.fmod.FMOD_Channel_SetLoopCount(ch, 0):
            self._notify('error', description='Cannot disable speech looping.')
            self.fmod.FMOD_Sound_Release(snd)
            return False
            
        # start the sound playing
        if self.fmod.FMOD_Channel_SetPaused(ch, False):
            self._notify('error', description='Cannot start speech.')
            self.fmod.FMOD_Sound_Release(snd)
            return False
            
        # store the playing channel
        self.fch = ch
        return True
        
    def _onFMODSyncPoint(self, index):
        if index == 0:
            # first marker is to notify about output start
            self._notify('started-output')
            if self.utterance is None:
                return
            try:
                if self.utterance.words[0][2] != 0:
                    # if first word is not on first sample, return; it's just
                    # the start marker
                    return
            except IndexError:
                return
        if self.utterance is None:
            return
        try:
            # notify about word info
            word = self.utterance.words.pop(0)
            self._notify('started-word', location=word[0], length=word[1])
        except IndexError:
            return