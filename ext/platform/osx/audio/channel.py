'''
Cocoa speech and sound interface.

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
import objc
from common.audio.fmodchannel import FMODChannelBase
from Foundation import *
from AppKit import *
from PyObjCTools import AppHelper

class ChannelController(NSObject, FMODChannelBase):
    def initWithId_Module_System_(self, ch_id, fmod, fsys):
        self = super(ChannelController, self).init()
        if self:
            # invoke base constructor manually since we're in NSObject land
            FMODChannelBase.__init__(self, ch_id, fmod, fsys)
            # speech synthesizer reference
            self.tts = None
            # first word flag
            self.first_word = False
        return self

    def _initializeConfig(self):
        FMODChannelBase._initializeConfig(self)
        self.config['voice'] = NSSpeechSynthesizer.defaultVoice()

    def shutdown(self, cmd):
        FMODChannelBase.shutdown(self, cmd)
        self.tts = None
    
    def reset(self, cmd):
        FMODChannelBase.reset(self, cmd)
        if self.tts:
            # reset tts if it exists
            self.tts.setVoice_(self.config['voice'])
            self.tts.setRate_(self.config['rate'])
            self.tts.setVolume_(self.config['volume'])

    def stop(self, cmd):
        FMODChannelBase.stop(self, cmd)
        if self.tts is not None:
            self.tts.stopSpeaking()
    
    def _outputUtterance(self, utterance):
        if not self.tts:
            # build a new synthesizer
            self.tts = NSSpeechSynthesizer.alloc().initWithVoice_(None)
            # register for callbacks
            self.tts.setDelegate_(self)
            # set initial properties
            self.tts.setVoice_(self.config['voice'])
            self.tts.setVolume_(self.config['volume'])
            self.tts.setRate_(self.config['rate'])
        # flag first word so we can notify on output start
        self.first_word = True
        # start speaking
        self.tts.startSpeakingString_(str(utterance.text))
        return True

    def _getVoices(self):
        FMODChannelBase._getVoices(self)
        return list(NSSpeechSynthesizer.availableVoices())

    def _setRate(self, val):
        FMODChannelBase._setRate(self, val)
        if self.tts:
            self.tts.setRate_(val)

    def _setVolume(self, val):
        FMODChannelBase._setVolume(self, val)
        if self.tts:
            self.tts.setVolume_(val)

    def _setVoice(self, val):
        FMODChannelBase._setVoice(self, val)
        if self.tts:
            self.tts.setVoice_(val)
            # have to reset volume and rate after changing voice
            self.tts.setVolume_(self.config['volume'])
            self.tts.setRate_(self.config['rate'])

    def speechSynthesizer_didFinishSpeaking_(self, tts, success):
        if self.first_word:
            self._notify('started-output')            
        self._notify(self.done_action)
        # reset stateful data
        self.first_word = False
        self.busy = False
        self.name = None
        # process the queue
        self._processQueue('finished speaking')

    def speechSynthesizer_willSpeakWord_ofString_(self, tts, rng, text):
        if self.first_word:
            self._notify('started-output')
            self.first_word = False
        self._notify('started-word', location=rng.location, length=rng.length)
