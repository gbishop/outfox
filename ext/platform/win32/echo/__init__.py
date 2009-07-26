'''
Echo service example for win32.

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
from common.echo.page import PageController
import asyncore
import os

RUNNING = True

def buildServer(module, port):
    return JSONServer(port)

def buildPage(module, page_id):
    return PageController(page_id, module)

def shutdown(module):
    module.RUNNING = False

def run(module):
    while module.RUNNING:
        # poll asyncore
        asyncore.poll(0.05)