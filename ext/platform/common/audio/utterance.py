'''
Speech utterance waveform and word metadata.

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

class Utterance(object):
    '''
    @ivar text String utterance
    @ivar samples Buffer of speech waveform samples
    @ivar rate Integer waveform sampling rate in Hz
    @ivar depth Integer sample bit depth in bits
    @ivar channels Integer waveform channel count
    @ivar words Array of (position, length, sample offset) tuples for words in
        the utterance
    '''
    def __init__(self, text, samples='', rate=44100, depth=16, channels=1, 
    words=[]):
        self.text = text
        self.samples = samples
        self.rate = rate
        self.depth = depth
        self.channels = channels
        self.words = words