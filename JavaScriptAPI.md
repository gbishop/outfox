# Overview #

The Outfox JavaScript client defines a core interface for starting and stopping services on the global _outfox_ singleton. The Outfox client attaches additional interfaces to this singleton as new service start and removes them as they stop.

# Outfox Deferreds #

Outfox uses deferred objects as a means to notify Web applications about responses to asynchronous requests. The Web application registers callbacks for deferred success notices and errbacks for deferred failure notices.

Every deferred instance has these methods:

` void outfox.Deferred.addCallback(callback_func) `

Call to add an observer for success notifications.

  * _(function) callback\_func_ The function to invoke upon success. The function takes a single parameter, the response object, provided by the caller. The name/value properties of the response depend on the purpose of the notification as documented below. The callback should return the parameter passed to it or another value which Outfox will provide to all further observers of this deferred.

` void outfox.Deferred.addErrback(callback_func) `

Call to add an observer for failure notifications.

  * _(function) callback\_func_ The function to invoke upon an error. The function takes a single parameter, the response object, provided by the caller. The name/value properties of the response depend on the purpose of the notification as documented below. The callback should return the parameter passed to it or another value which Outfox will provide to all further observers of this deferred.

# Outfox Core #

The core interface defines methods for initializing Outfox; starting and stopping services; and adding and removing response observers.

` outfox.Deferred outfox.init(box, encode_json, decode_json) `

Call to initialize Outfox.

  * _(object) box_ The DOM node in which Outfox will create its request and response queues.
  * _(function) encode\_json_ The function Outfox will invoke to encode JSON data.
  * _(function) decode\_json_ The function Outfox will invoke to decode JSON data.

The return value is a deferred notification. The deferred callback receives an object with these properties:

  * _(string) version_ The major.minor.release version number of the Outfox add-on the user has installed.

The deferred errback receives an object with these properties:

  * _(string) description_ Reason why Outfox failed to initialize.

` outfox.Deferred outfox.startService(name) `

Call to start a service.

  * _(string) name_ The name of the service Outfox will start.

The return value is a deferred notification of when the service is ready for use. The deferred callback receives an object with these properties:

  * _(string) service_ The name of the service started.
  * _(string) extension_ A string of JavaScript code that will be evaluted and attached as an object under the name _outfox.SERVICENAME_.

The deferred errback receives an object with these properties:

  * _(string) service_ The name of the service that failed to start.
  * _(string) description_ The reason why the service failed to start.

` outfox.Deferred outfox.stopService(name) `

Call to stop a service.

  * _(string) name_ The name of the service Outfox will stop.

The return value is a deferred notification of when the service is no longer available. The deferred callback receives an object with these properties:

  * _(string) service_ The name of the service that stopped.

The deferred errback is never invoked when stopping.

` object outfox.addObserver(ob, service) `

Call to add an observer for responses from the given service.

  * _(function) ob_ The observer callback function.
  * _(string) service_ The name of the service to observe for responses.

The return value is an opaque token the caller should store to later unregister the observer. The observer callback receives the following parameters when invoked:

  * _(object) outfox_ The Outfox object.
  * _(object) command_ The response from the service. The name/value properties on this object depend on the service and the purpose of the response.

` void outfox.removeObserver(token) `

Call to remove an observer.

  * _(opaque) token_ is the return value from _addObserver_ corresponding to the observer to remove.

# Outfox Services #

## Audio Service ##

The audio interface defines methods for playing sounds, synthesizing speech, configuring output, and receiving callbacks on utterance start, utterance end, and individual words.

` void outfox.audio.say(text, channel, name) `

Call to speak a string or queue it if the channel is busy.

  * _(string) text_ The text to speak.
  * _(integer) channel_ The serial output channel to use to speak the text (default: 0).
  * _(string) name_ A string to include on all response messages related to this say operation (default: none).

` void outfox.audio.play(url, channel, name) `

Call to play a sound or queue it if the channel is busy.

  * _(string) url_ The relative or absolute location of the sound to play.
  * _(integer) channel_ The serial output channel to use to play the sound (default: 0).
  * _(string) name_ A string to include on all response messages related to this say operation (default: none).

A play command instructs Outfox to download a complete sound file to the browser cache and decode it entirely in memory before beginning output. This works well for small sound files or files that will play repeatedly. To play larger files, use the stream command. If Outfox fails to cache a file, it will switch to streaming it automatically.

The play command supports every format supported by FMOD Ex. See the File Format Support heading on the [FMOD Ex Feature List](http://www.fmod.org/index.php/products/fmodexdetailed) page for a complete list. Sound files can contain waveforms with any sampling rate, bit depth, or number of channels.

` void outfox.audio.stream(url, channel, name) `

Call to stream a sound or queue it if the channel is busy.

  * _(string) url_ The relative or absolute location of the sound to play.
  * _(integer) channel_ The serial output channel to use to play the sound (default: 0).
  * _(string) name_ A string to include on all response messages related to this say operation (default: none).

A stream command instructs Outfox to download, decode, and playback chunks of a sound at a time. This works well for large sound files or those that will not play often as streamed file are not cached on local disk. To play small files, use the play command.

The stream command supports every format supported by FMOD Ex. See the File Format Support heading on the [FMOD Ex Feature List](http://www.fmod.org/index.php/products/fmodexdetailed) page for a complete list. Sound files can contain waveforms with any sampling rate, bit depth, or number of channels.

` void outfox.audio.stop(channel) `

Call to stop output and clear all queued messages.

  * _(integer) channel_ The ID of the channel to stop.

` void outfox.audio.setPropertyNow(name, value, channel) `

Call to configure a channel property immediately, even while a channel is busy.

  * _(string) name_ The name of the property to configure.
  * _(any) value_ The new value to set for the property.
  * _(integer) channel_ The serial output channel to configure (default: 0).

` void outfox.audio.setProperty(name, value, channel) `

Call to configure a channel property or queue the configuration if the channel is busy.

  * _(string) name_ The name of the property to configure.
  * _(any) value_ The new value to set for the property.
  * _(integer) channel_ The serial output channel to configure (default: 0).

` any outfox.audio.getProperty(name, channel) `

Call to retrieve a channel property value.

  * _(string) name_ The name of the property to query.
  * _(integer) channel_ The serial output channel to query (default: 0).

The return value is the current value of the named property.

` void outfox.audio.resetNow(channel) `

Call to reset the channel to its default properties immediately even while a channel is busy.

  * _(integer) channel_ The serial output channel to reset (default: 0).

` void outfox.audio.reset(channel) `

Call to reset the channel to its default properties or queue the reset if the channel is busy.

  * _(integer) channel_ The serial output channel to reset (default: 0).

` outfox.Deferred precache(urls) `

Call to cache the contents of all of the given URLs.

  * _(array) urls_ The array of string URLs.

The return value is a deferred notification of when the content of all of the value URLs has been fetched.

This method is particularly useful for guaranteeing a set of sounds is local before attempting to play any of them. If any URL is bad or cannot be fetched, it is simply ignored.

### Properties ###

The sound interface supports the getting and setting of the following baseline properties across platforms:

  * _(int) rate_ The speech rate in words per minute for the channel.
  * _(float) volume_ The volume percentage between 0.0 and 1.0 for the channel.
  * _(string) voice_ The name of a voice to use for synthesis on the channel.
  * _(boolean) loop_ The flag that sets if all sounds loop indefinitely on a channel (true) or play once and only once (false). This property only applies to play commands, not stream or say.

Web applications can also get, but not set, the value of the following property:

  * _(array) voices_ The list of all available voice names.

### Callbacks ###

The audio interface supports a set of baseline callbacks across platforms. All callback functions receive one parameter, a response object with properties corresponding to the server to client JSON messages specified on the [JSONProtocol](JSONProtocol.md) page. The audio interface provides two additional methods to assist with the registering and unregistering of observers of audio messages.

` object outfox.audio.addObserver(ob, channel, actions) `

Call to add an observer for responses from the audio service.

  * _(function) ob_ The observer callback function
  * _(integer) channel_ The ID of the channel to observe for responses (default: 0).
  * _(array) action_ An array of string action names to observe (default: all actions).

The return value is an opaque token the caller should store to later unregister the observer.

` void outfox.audio.removeObserver(token) `

Call to remove an audio observer.

  * _(opaque) token_ The return value from _addObserver_ corresponding to the observer to remove.