'''
Channel shared interface to espeak singleton.

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
from espeak import *
import Numeric
import pygame.sndarray

# init speech synth
ESPEAK_RATE = Initialize(AUDIO_OUTPUT_SYNCHRONOUS, 500)
# get default voice
DEFAULT_VOICE = GetCurrentVoice().contents.name
# seems to be fixed
ESPEAK_BITS = 16
ESPEAK_CHANNELS = 1 

def SynthWords(text, mixer_rate=44100, mixer_bits=16, mixer_channels=2):
    # stores bytes
    chunks = []
    # stores 3-tuples of text position, text length, and sample position
    meta = []
    # consider difference between espeak rate, bits, and channels and the mixer
    # rate, bits, and channels
    rate_mult = mixer_rate/ESPEAK_RATE
    bits_mult = mixer_bits/ESPEAK_BITS
    ch_mult = mixer_channels/ESPEAK_CHANNELS

    def synth_cb(wav, numsample, events):
        if numsample > 0:
            # always 16 bit samples
            chunk = ctypes.string_at(wav, numsample*2)
            chunks.append(chunk)
        # store all events for later processing
        i = 0
        while True:
            event = events[i]
            if event.type == EVENT_LIST_TERMINATED:
                break
            elif event.type == EVENT_WORD:
                # position seems to be 1 based, not 0
                meta.append((event.text_position-1, event.length, 
                             event.sample * rate_mult))
            i += 1
        return 0

    # register the callback and do the synthesis
    SetSynthCallback(synth_cb)
    Synth(text)

    # make sure we synthed at least one word
    if len(meta) == 0:
        return None, []

    # create a sound from the data
    buff = Numeric.fromstring(''.join(chunks), Numeric.Int16)
    buff = Numeric.repeat(buff, rate_mult*ch_mult*bits_mult)
    buff = Numeric.reshape(buff, (-1, 2))
    snd = pygame.sndarray.make_sound(buff)
    return snd, meta
