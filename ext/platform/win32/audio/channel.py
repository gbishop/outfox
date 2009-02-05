'''
SAPI and FMOD speech and sound interface.

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
import math
import ctypes
import pyTTS as tts
from common.audio.utterance import Utterance
from common.audio.fmodspeech import FMODSpeechBase

# exponential regression for wpm; MSMary values used as defaults for unknown
# voices
E_REG = {'MSSam' : (137.89, 1.11),
         'MSMary' : (156.63, 1.11),
         'MSMike' : (154.37, 1.11)}

class ChannelController(FMODSpeechBase):
    def __init__(self, ch_id, fmod, fsys):
        # build speech synth
        self.tts = tts.Create(output=False)
        self.tts.SetOutputFormat(22, 16, 1)
        # store default voice
        self.default_voice = self.tts.Voice
        # initialize base class after default voice is known
        FMODSpeechBase.__init__(self, ch_id, fmod, fsys)
        # set tts defaults
        self.tts.Voice = self.config['voice']
        a, b = E_REG.get(self.tts.Voice, E_REG['MSMary'])
        self.tts.Rate = int(math.log(self.config['rate']/a, b))
    
    def _initializeConfig(self):
        FMODSpeechBase._initializeConfig(self)
        self.config['voice'] = self.default_voice

    def shutdown(self, cmd):
        FMODSpeechBase.shutdown(self, cmd)
        self.tts = None

    def reset(self, cmd):
        FMODSpeechBase.reset(self, cmd)
        self._setSpeechVoice(self.default_voice)
        
    def _getVoices(self):
        return self.tts.GetVoiceNames()

    def _setSpeechRate(self, val):
        a, b = E_REG.get(self.tts.Voice, E_REG['MSMary'])
        self.tts.Rate = int(math.log(val/a, b))

    def _setSpeechVoice(self, val):
        self.tts.Voice = val
        a, b = E_REG.get(self.tts.Voice, E_REG['MSMary'])
        # adjust the rate based on the new voice
        self.tts.Rate = int(math.log(self.config['rate']/a, b))

    def _synthesizeUtterance(self, text):
        # synthesize speech and events
        stream, events = tts.Speak(text)

        # return an empty utterance if we didn't synth any words
        if len(events) == 0:
            return Utterance(text)

        # get the waveform format information
        format = stream.Format.GetWaveFormatEx()

        # get word information
        meta = [(e.CharacterPosition, e.Length, e.StreamPosition)
            for e in events if e.EventType == tts.tts_event_word]
        
        # populate an utterance object
        samples = stream.GetData()
        return Utterance(text, samples, format.SamplesPerSec, 
            format.BitsPerSample, format.Channels, meta)