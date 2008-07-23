import time, os
os.environ["SDL_VIDEODRIVER"] = "dummy"
import espeak
import ctypes
import Numeric
import pygame.mixer
import pygame.display

rate = espeak.Initialize(espeak.AUDIO_OUTPUT_SYNCHRONOUS, 500)
pygame.mixer.init(44100,-16,2,4096)
pygame.mixer.set_num_channels(256)
pygame.init()

chunks = []
meta = []
def synth_cb(wav, numsample, events):
    if numsample > 0:
        # 16 bit samples
        chunk = ctypes.string_at(wav, numsample*2)
        chunks.append(chunk)
    # store all events for later processing
    i = 0
    while True:
        event = events[i]
        if event.type == espeak.EVENT_LIST_TERMINATED:
            break
        elif event.type == espeak.EVENT_WORD:
            meta.append((event.text_position, event.length, event.sample*2))
        i += 1
    return 0

espeak.SetSynthCallback(synth_cb)
espeak.Synth(u'When I speak through pygame, I hear a bit of a crackle within words.')

# split into word chunks
words = []
data = ''.join(chunks)
start = meta[0][2]
x = len(meta) - 1
if x >= 0:
    for i in xrange(x):
        stream_pos = meta[i+1][2]
        buff = Numeric.fromstring(data[start:stream_pos], Numeric.Int16)
        buff = Numeric.reshape(Numeric.repeat(buff, 4), (-1, 2))
        snd = pygame.sndarray.make_sound(buff)
        words.append((snd, meta[i][0], meta[i][1]))
        start = stream_pos
    buff = Numeric.fromstring(data[start:], Numeric.Int16)
    buff = Numeric.reshape(Numeric.repeat(buff, 4), (-1, 2))
    snd = pygame.sndarray.make_sound(buff)
    words.append((snd, meta[x][0], meta[x][1]))
else:
    # nothing to speak, so fake a word
    words.append(('', None, None))

ch = pygame.mixer.find_channel()
ch.set_endevent(pygame.USEREVENT)
i = 0
import time
while i < len(words):
    print 'location', words[i][1], 'length', words[i][2]
    ch.play(words[i][0])
    event = pygame.event.wait()
    i += 1
