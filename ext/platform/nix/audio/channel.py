'''
espeak and pygame speech and sound interface.

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
import ctypes
import espeak
from common.audio.utterance import Utterance
from common.audio.fmodspeech import FMODSpeechBase

class ChannelController(FMODSpeechBase):
    def __init__(self, ch_id, fmod, fsys):
        self.tts = espeak
        # init speech synth
        self.sampling_rate = self.tts.Initialize(espeak.AUDIO_OUTPUT_SYNCHRONOUS, 500)
        # get default voice
        self.default_voice = self.tts.GetCurrentVoice().contents.name
        # initialize base class after default voice is known
        FMODSpeechBase.__init__(self, ch_id, fmod, fsys)
        # set tts defaults
        self.tts.SetVoiceByName(self.default_voice)
        self.tts.SetParameter(self.tts.RATE, self.config['rate'])
    
    def _initializeConfig(self):
        FMODSpeechBase._initializeConfig(self)
        self.config['voice'] = self.default_voice

    def shutdown(self, cmd):
        FMODSpeechBase.shutdown(self, cmd)
        self.tts = None

    def reset(self, cmd):
        FMODSpeechBase.reset(self, cmd)
        self.tts.SetVoiceByName(self.default_voice)
        self.tts.SetParameter(self.tts.RATE, self.config['rate'])

    def _getVoices(self):
        FMODSpeechBase._getVoices(self)
        return [v.name for v in self.tts.ListVoices()]

    def _setRate(self, val):
        FMODSpeechBase._setRate(self, val)
        self.tts.SetParameter(self.tts.RATE, val)

    def _setVoice(self, val):
        FMODSpeechBase._setVoice(self, val)
        self.tts.SetVoiceByName(val)

    def _synthesizeUtterance(self, text):
        # stores bytes
        chunks = []
        # stores 3-tuples of text position, text length, and sample position
        meta = []

        def synth_cb(wav, numsample, events):
            if numsample > 0:
                # always 16 bit samples
                chunk = ctypes.string_at(wav, numsample*2)
                chunks.append(chunk)
            # store all events for later processing
            i = 0
            while True:
                event = events[i]
                if event.type == self.tts.EVENT_LIST_TERMINATED:
                    break
                elif event.type == self.tts.EVENT_WORD and event.length > 0:
                    # ignore zero length words
                    # position seems to be 1 based, not 0
                    meta.append((event.text_position-1, event.length, event.sample))
                i += 1
            return 0

        # register the callback and do the synthesis
        self.tts.SetSynthCallback(synth_cb)
        self.tts.Synth(text)

        if len(meta) == 0:
            # return an empty utterance if we didn't synth any words
            return Utterance(text)

        # populate an utterance object
        samples = ''.join(chunks)
        return Utterance(text, samples, self.sampling_rate, 16, 1, meta)