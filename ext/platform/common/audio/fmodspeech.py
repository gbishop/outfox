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
from fmodchannel import FMODChannelBase

FMOD_CHANNEL_FREE = -1
FMOD_SOUND_FORMAT_PCM8 = 1
FMOD_SOUND_FORMAT_PCM16 = 2
FMOD_OPENMEMORY = 0x00000800
FMOD_OPENRAW = 0x00001000
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
        ('nonblockcallback', c_void_p),
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
            
        # set word markers on the sound
        pt = c_void_p()
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
        word = self.utterance.words.pop(0)
        self._notify('started-word', location=word[0], length=word[1])