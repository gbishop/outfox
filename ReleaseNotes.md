# Version 0.4.x Series #

## Version 0.4.1 ##

  * Added example "echo" service

## Version 0.4.0 ##

  * Site white and black listing (http://code.google.com/p/outfox/issues/detail?id=47&can=1)
    * Added message prompting user to allow/deny site access to Outfox on a (scheme, host, port) basis (a HTML5 origin).
    * Added an options dialog under Add-ons where the user can manage saved allow/deny decisions per site.
    * Added a errback from the outfox.init() method when access to Outfox is denied.

# Version 0.3.x Series #

## Version 0.3.5 ##

  * Fixed wrong context when creating outfox objects outside normal browser window (Greasemonkey) (http://code.google.com/p/outfox/issues/detail?id=48&can=1)

## Version 0.3.4 ##

  * Updated version number compatibility to account for Firefox 3.5.x

## Version 0.3.3 ##

  * Noted that stream looping is not supported, only looping for play (http://code.google.com/p/outfox/issues/detail?id=40&can=1)
  * Fixed exception passing int instead of string to say on OS X (http://code.google.com/p/outfox/issues/detail?id=41&can=1)
  * Fixed utterances blending together on Linux by enabling end pause flag in espeak (http://code.google.com/p/outfox/issues/detail?id=42&can=1)
  * Fixed crossplatform differences in how silent utterance callbacks are handled (http://code.google.com/p/outfox/issues/detail?id=43&can=1)
  * Fixed wrong encoding again on text for OS X speech (http://code.google.com/p/outfox/issues/detail?id=44&can=1)
  * Fixed a pyobjc memory leak on OS X (http://code.google.com/p/outfox/issues/detail?id=45&can=1)
  * Fixed stream() call crashes outfox on Win32 (http://code.google.com/p/outfox/issues/detail?id=46&can=1)

## Version 0.3.2 ##

  * Fixed Mac error decoding utf-8 to unicode for speech (http://code.google.com/p/outfox/issues/detail?id=38&can=1)
  * Fixed cross-channel blocking behavior when opening sounds (http://code.google.com/p/outfox/issues/detail?id=39&can=1)

## Version 0.3.1 ##

  * Fixed short sound playback (http://code.google.com/p/outfox/issues/detail?id=33&can=1)
  * Fixed short sounds fail to cache with in-memory cache (http://code.google.com/p/outfox/issues/detail?id=34&can=1)
  * Fixed deadlock caching same file concurrently from two play requests (http://code.google.com/p/outfox/issues/detail?id=35&can=1)
  * Fixed unit tests to account for 0.3.0 differences in JSON protocol (http://code.google.com/p/outfox/issues/detail?id=36&can=1)
  * Added bug tests (http://code.google.com/p/outfox/issues/detail?id=36&can=1)
  * Fixed failure to handle service exceptions (http://code.google.com/p/outfox/issues/detail?id=37&can=1)

## Version 0.3.0 ##

  * Switched to using FMOD for audio instead of pymedia+pygame+SDL (http://code.google.com/p/outfox/issues/detail?id=30&can=1)
  * Added support for relative sound URLs
  * Added support for streaming large sound files (http://code.google.com/p/outfox/issues/detail?id=27&can=1)
  * Fixed playback of sounds of any sampling rate, bit depth, channel count (http://code.google.com/p/outfox/issues/detail?id=25&can=1)
  * Added started-output notification when actual audio output begins for say, play, stream, so on (http://code.google.com/p/outfox/issues/detail?id=32&can=1)

Developers should read the new [license terms](LicenseTerms.md) governing the use of Outfox Audio with FMOD Ex in their applications.

# Version 0.2.x Series #

## Version 0.2.1 ##

  * Fixed say() on Mac stops prematurely (http://code.google.com/p/outfox/issues/detail?id=23&can=1)
  * Added precache() method to cache multiple sound files locally before playback (http://code.google.com/p/outfox/issues/detail?id=26&can=1)
  * Fixed passing integer to say() causes exception on mac (http://code.google.com/p/outfox/issues/detail?id=29&can=1)
  * Made version number available to JS on initialization (http://code.google.com/p/outfox/issues/detail?id=28&can=1)
  * Fixed outfox.Deferred class bugs

## Version 0.2.0 ##

  * Refactored entire code base to support dynamic loading/unloading of installed services (http://code.google.com/p/outfox/issues/detail?id=14&can=1, http://code.google.com/p/outfox/issues/detail?id=17&can=1, http://code.google.com/p/outfox/issues/detail?id=18&can=1, http://code.google.com/p/outfox/issues/detail?id=19&can=1)
  * Support filtering of audio messages by action (http://code.google.com/p/outfox/issues/detail?id=15&can=1)
  * Better error handling during service start (http://code.google.com/p/outfox/issues/detail?id=21&can=1)
  * Better error handling for bad sound URLs (http://code.google.com/p/outfox/issues/detail?id=20&can=1)
  * Fixed voice switching failing on Windows (http://code.google.com/p/outfox/issues/detail?id=22&can=1)

# Version 0.1.x Series #

## Version 0.1.2 ##

  * Concurrent speech/sound on Vista now works (http://code.google.com/p/outfox/issues/detail?id=8&can=1)
  * Switched from chunking speech into words for callbacks to giving word callbacks at approximate times. Speech is much smoother on win/ nix now. (http://code.google.com/p/outfox/issues/detail?id=13&can=1)

## Version 0.1.1 ##

  * Outfox now uses the Firefox cache for sound files. (http://code.google.com/p/outfox/issues/detail?id=2&can=1&q=status:Fixed)
  * Windows and Linix platforms now resample MP3 files to 44.1kHz so they
play properly. (http://code.google.com/p/outfox/issues/detail?id=4&can=1&q=status:Fixed)

## Version 0.1.0 ##

  * First release with basic speech and sound support.