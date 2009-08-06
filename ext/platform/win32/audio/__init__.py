'''
Asyncore socket server, SAPI speech, and FMOD sound/mixer for Windows.

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
from common.server import JSONServer
from common.audio.channel import ChannelBase
from common.audio.page import PageController
import channel
import asyncore
import os
from ctypes import *

# audio specific resources
FMOD_MODULE = None
FMOD_SYSTEM = c_void_p()
RUNNING = True

def buildChannel(module, ch_id):
    return channel.ChannelController(ch_id, FMOD_MODULE, FMOD_SYSTEM)

# common service functions
def buildServer(module, port):
    return JSONServer(port)

def buildPage(module, page_id):
    return PageController(page_id, module)

def shutdown(module):
    module.RUNNING = False

def run(module):
    # load the FMOD dynamic lib, adjusting for py2exe build location
    #lib = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'fmodex.dll')
    lib = 'fmodex.dll'
    lib = os.path.abspath(lib)
    fmod = windll.LoadLibrary(lib)
    # create a global FMOD system object
    if fmod.FMOD_System_Create(byref(FMOD_SYSTEM)):
        raise RuntimeError
    if fmod.FMOD_System_Init(FMOD_SYSTEM, 128, 0, None):
        raise RuntimeError
    # store FMOD globally for channels
    module.FMOD_MODULE = fmod
    
    # main event loop polls json server and FMOD
    i = 0
    while module.RUNNING:
        # poll asyncore
        asyncore.poll(0.05)
        try:
            # poll FMOD
            fmod.FMOD_System_Update(FMOD_SYSTEM)
        except Exception:
            pass
        # pump channels that are idle
        ChannelBase.processPending()
    
    # cleanup
    fmod.FMOD_System_Release(FMOD_SYSTEM)
