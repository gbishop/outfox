'''
Asyncore socket server, SAPI speech, and pygame sound/mixer for Windows.

Copyright (c) 2008 Wayne Ian Clark

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
import os
# need this to run pygame headless
os.environ["SDL_VIDEODRIVER"] = "dummy"
from common.server import JSONServer
import channel
import asyncore
import threading
import pygame.event
import pygame.display
import pygame.locals

def buildServer(port):
    return JSONServer(port)

def buildChannel(ch_id):
    return channel.ChannelController(ch_id)

def quit():
    event = pygame.event.Event(pygame.QUIT)
    pygame.event.post(event)

def run():
    # have to init the damn display system to use sound, ugh
    pygame.display.init()
    # start the server thread with a timeout value
    ts = threading.Thread(target=asyncore.loop, args=[2])
    ts.start()
    # pygame event loop
    while 1:
        # wait for an event
        event = pygame.event.wait()
        if event.type == channel.EVT_PROCESS_REQUEST:
            # handle a request pushed to a channel
            try:
                event.channel.onProcessRequest(event.command)
            except Exception, e:
                # print and consume exceptions
                print e
        elif event.type == pygame.locals.QUIT:
            # exit the event loop
            return
        else:
            # treat all other events as player completion
            # pass them to channel based on event type 
            # would be much easier if we could specify sound event properties...
            ch = channel.getChannelFromId(event.type)
            try:
                ch.onPlayerComplete()
            except Exception, e:
                print e
