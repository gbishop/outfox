'''
Cocoa-based socket server, speech, and FMOD mixer for OS X 10.5 and higher.

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
import os
from common.audio.channel import ChannelBase
from ..server import JSONServer
from common.audio.page import PageController
from channel import ChannelController
from PyObjCTools import AppHelper
from Foundation import NSTimer
from ctypes import *

FMOD_MODULE = None
FMOD_SYSTEM = c_void_p()

class FMODTimer(object):
    def __init__(self, delay):
        self.timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
        delay, self, 'onTimer:', None, True)

    def onTimer_(self, timer):
        if FMOD_SYSTEM is not None:
            try:
                # update the FMOD system
                FMOD_MODULE.FMOD_System_Update(FMOD_SYSTEM)
            except Exception:
                pass
        # pump idle channels
        [ch._processQueue() for ch in ChannelBase.toProcess]

def buildServer(module, port):
    return JSONServer.alloc().initWithPort_(port)

def buildPage(module, page_id):
    return PageController(page_id, module)

def buildChannel(module, ch_id):
    return ChannelController.alloc().initWithId_Module_System_(ch_id, 
        FMOD_MODULE, FMOD_SYSTEM)

def run(module):
    global FMOD_SYSTEM
    path = os.path.join(os.path.dirname(__file__), 'libfmodex.dylib')
    # load the FMOD dynamic lib
    fmod = cdll.LoadLibrary(path)
    # create a global FMOD system object
    if fmod.FMOD_System_Create(byref(FMOD_SYSTEM)):
        raise RuntimeError
    if fmod.FMOD_System_Init(FMOD_SYSTEM, 128, 0, None):
        raise RuntimeError
    # store FMOD globally for channels
    module.FMOD_MODULE = fmod
    # register timer for FMOD updates
    ftimer = FMODTimer(0.05)
    # enter the main event loop
    AppHelper.runConsoleEventLoop()
    # cleanup
    fmod.FMOD_System_Release(FMOD_SYSTEM)
    FMOD_SYSTEM = None

def shutdown(module):
    AppHelper.stopEventLoop()