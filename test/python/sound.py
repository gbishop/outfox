import time, os
os.environ["SDL_VIDEODRIVER"] = "dummy"
import pymedia.audio.acodec
import pymedia.muxer
import Numeric
import pygame.sndarray
import pygame.mixer
import pygame.display

pygame.mixer.quit()
pygame.mixer.init(44100, -16, 2)
print pygame.mixer.get_init()
pygame.mixer.set_num_channels(256)
print pygame.mixer.get_num_channels()
pygame.init()

dm = pymedia.muxer.Demuxer('mp3')
f = file('bell.mp3', 'rb')
try:
    print 'trying pygame'
    snd = pygame.mixer.Sound(f)
except pygame.error:
    s = f.read()
    frames = dm.parse(s)
    dec = pymedia.audio.acodec.Decoder(dm.streams[0])
    segs = []
    for fr in frames:
        r = dec.decode(fr[1])
        if r and r.data:
            seg = Numeric.fromstring(str(r.data), Numeric.Int16)
            segs.append(seg)

    buff = Numeric.concatenate(segs)
    buff = Numeric.reshape(Numeric.repeat(buff, 2/r.channels), (-1, 2))
    ch = pygame.mixer.find_channel()
    snd = pygame.sndarray.make_sound(buff)
ch.set_endevent(pygame.USEREVENT)
ch.play(snd)
event = pygame.event.wait()
print 'done'
