'''
Interface to SAPI with pygame output.

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
from pyTTS import *
import Numeric
import pygame.sndarray

def SynthWords(tts, text, mixer_rate=44100, mixer_bits=16, mixer_channels=2):
    # synthesize speech and events
    stream, events = tts.Speak(text)

    # make sure we synthed at least one word
    if len(events) == 0:
        return None, []

    # get the waveform format information
    format = stream.Format.GetWaveFormatEx()

    # consider difference between espeak rate, bits, and channels and the mixer
    # rate, bits, and channels
    rate_mult = mixer_rate/format.SamplesPerSec
    bits_mult = mixer_bits/format.BitsPerSample
    ch_mult = mixer_channels/format.Channels

    # correct metadata for new sampling rate
    # @todo: note sure what StreamPosition units are in general, just using 
    #   what works from experimentation
    meta = [(e.CharacterPosition, e.Length, e.StreamPosition / ch_mult)
            for e in events if e.EventType == tts_event_word]

    # create a sound from the data
    buff = Numeric.fromstring(stream.GetData(), Numeric.Int16)
    buff = Numeric.repeat(buff, rate_mult*ch_mult*bits_mult)
    buff = Numeric.reshape(buff, (-1, 2))
    snd = pygame.sndarray.make_sound(buff)
    return snd, meta
