import time, os
os.environ["SDL_VIDEODRIVER"] = "dummy"
import pyTTS
import Numeric
import pygame.sndarray
import pygame.mixer
import pygame.display

go = True

pygame.init()
pygame.mixer.quit()
tts = pyTTS.Create(output=False)
tts.SetOutputFormat(44, 16, 1)
tts.Voice = 'MSMary'
stream, events = tts.Speak('My name is Sam', pyTTS.tts_is_xml)
format = stream.Format.GetWaveFormatEx()
pygame.mixer.init(format.SamplesPerSec, format.BitsPerSample, 2)
print pygame.mixer.get_init()
pygame.mixer.set_num_channels(256)
print pygame.mixer.get_num_channels()
stream, events = tts.Speak(u'Windows is the worst platform ever.')
#snd = pygame.mixer.Sound(stream.GetData())
#p1 = pygame.mixer.find_channel()
#p1.set_endevent(pygame.USEREVENT)
#p1.play(snd)
#time.sleep(0.5)
#p2 = pygame.mixer.find_channel()
#p2.set_endevent(pygame.USEREVENT+1)
#p2.play(snd)
#event = pygame.event.wait()
#print event.type
#event = pygame.event.wait()
#print event.type

pos =  [(e.CharacterPosition, e.Length, e.StreamPosition) for e in events if e.EventType == 5]
sounds = []
start = pos[0][2]
data = stream.GetData()
for cp, cl, sp in pos[1:]:
    buff = data[start:sp]
    buff = Numeric.fromstring(buff, Numeric.Int16)
    buff = Numeric.reshape(Numeric.repeat(buff, 2), (-1, 2))
    snd = pygame.sndarray.make_sound(buff)
    sounds.append(snd)
    start = sp
buff = Numeric.fromstring(data[start:], Numeric.Int16)
buff = Numeric.reshape(Numeric.repeat(buff, 2), (-1, 2))
snd = pygame.sndarray.make_sound(buff)
sounds.append(snd)

print 'done'
ch = pygame.mixer.find_channel()
ch.set_endevent(pygame.USEREVENT)
i = 0
while i < len(sounds):
    print i, len(sounds), pos[i]
    snd = sounds[i]
    ch.play(snd)
    event = pygame.event.wait()
    i += 1
