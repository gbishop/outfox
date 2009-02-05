#!/usr/bin/env python
'''
Build script for Windows.

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
from distutils.core import setup
import py2exe
import shutil

dll_excludes = []
excludes = [
    'bz2',
    '_ssl',
    '_hashlib'
]
typelibs = [('{C866CA3A-32F7-11D2-9602-00C04F8EE628}', 0, 5, 0)]
packages = ['encodings', 'win32', 'common', 'simplejson']

setup(console=["outfox.py"],
      version='0.3.0',
      options={"py2exe": {"compressed": 1,
                          'optimize': 2,
                          'excludes' : excludes,
                          'dll_excludes': dll_excludes,
                          'typelibs': typelibs,
                          'packages': packages,
                          'bundle_files' : 1
                          }}
)