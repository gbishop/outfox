from distutils.core import setup
import py2exe
import shutil
import tempfile
import os

dll_excludes = []
excludes = [ 'bz2', '_ssl', '_hashlib' ]
typelibs = [('{C866CA3A-32F7-11D2-9602-00C04F8EE628}', 0, 5, 0)]
packages = ['encodings']

nwd = tempfile.mkdtemp()

print 'build in', nwd

if os.path.exists('dist'):
    shutil.rmtree('dist')

setup(console=["win32/mypython.py"],
      version="1.0",
      data_files = [('', ['win32/audio/fmodex.dll'])],
      options={'py2exe': {"compressed": 1,
                          "optimize": 2,
                          "excludes": excludes,
                          "dll_excludes": dll_excludes,
                          'typelibs': typelibs,
                          'packages': packages,
                          'dist_dir': nwd,
                          }}
      )

shutil.copytree(nwd, 'dist')
shutil.rmtree(nwd)
