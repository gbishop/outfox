# Get the Source #

See the _Source_ tab, _Checkout_ section on this website.

# Configure Firefox #

Follow the instructions in the [Mozilla Developer Center](http://developer.mozilla.org/en/docs/Setting_up_extension_development_environment) to configure a development environment. For the step entitled _Custom code location_, create a text file in your profiles directory named _outfox@code.google.com_ containing the path to the _ext_ folder in your source code sandbox.

# Install Pre-requisites #

This information is current as of the 0.3.0 release of Outfox supporting speech and sound only.

## OS X ##

The following libraries are required for the development of Outfox on OS X Leopard.

  * FMOD Ex 4.22

Place the _libfmodex.dylib_ file in the _ext/platform/osx/audio_ folder.

## Windows ##

The XPI package contains a binary executable for Windows. You must install the following libraries on Windows in order to build Windows binaries from your source sandbox.

  * python-2.5
  * py2exe-0.6.8
  * pywin32-210
  * pyTTS-3.0 (Unicode fix required in sapi.py. pyTTS author emailed. Look for 3.1 release.)
  * FMOD Ex 4.22

Place the _fmodex.dll_ file in the _ext/platform/win/audio_ folder.

After making changes to files in the _win32_ directory, you must build a new _outfox.exe_ using py2exe before testing in Firefox. Use the _setup.py_ file in _ext/platform_ to do so.

` python setup.py py2exe `

## Linux ##

The following packages are required for the development of Outfox on Linux distros.

  * python-2.5
  * espeak-1.36 or higher
  * FMOD Ex 4.22

Place the _libfmodex-4.22.02.so_ file in the _ext/platform/nix/audio_ folder.

# Test Your Environment #

  1. Put the root of your source sandbox in a web accessible location.
  1. Visit the _test/samples/index.html_ file in Firefox.
  1. If the _Run_ buttons on the page light up, Outfox has loaded properly and the tests are available. (The first one you run may be slow to start because components are loaded on demand.)
  1. If the _Run_ buttons remain disabled, check for an error at the top of the page just under the topmost heading. Also check the Firefox JavaScript console for error messages.