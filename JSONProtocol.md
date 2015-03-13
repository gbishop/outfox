# Message Format #

All messages sent from the browser JavaScript to the external server and vice versa are encoded in JSON format. A message consists of an envelope and a command. The envelope contains information needed by Outfox to route the command appropriately. It follows the format below:

` {"page_id" : <int>, "cmd" : <command data>} `

The Outfox JavaScript library and the server dispatcher strip the envelope from the command before invoking browser or server handlers. The JavaScript code and server only need to deal with commands as a result.

# Command Format #

All commands consist of a service name, an action name, and zero or more name/value pairs. The format is the following:

` {"service" : <string>, "action" : <string>, ["key" : value, ...]} `

# Startup Commands #

## Extension to Browser ##

  * ` {"action" : "initialized-outfox", "version" : <string>} `
  * ` {"action" : "failed-outfox", "description" : <string>} `

# Service Management Commands #

## Browser to Server ##

  * ` {"action" : "start-service", "service" : <string>} `
  * ` {"action" : "stop-service", "service" : <string>} `

## Server to Browser ##

  * ` {"action" : "started-service", "service" : <string>, "extension" : <string>} `
  * ` {"action" : "stopped-service", "service" : <string>} `
  * ` {"action" : "failed-service", "description" : <string>, "service" : <string>} `


## Audio Server Commands ##

The following commands form the protocol for the audio server plug-in for Outfox. In addition to the name / value pairs listed below, each command includes the pair "service" : "audio" which is omitted for brevity.

## Browser to Server ##

  * ` {"action" : "say", "channel" : <integer>, "text" : <string>, ["name" : <string>]} `
  * ` {"action" : "play", "channel" : <integer>, "url" : <string>, ["cache", <boolean>, "name" : <string>]} `
  * ` {"action" : "stream", "channel" : <integer>, "url" : <string>, ["cache", <boolean>, "name" : <string>]} `
  * ` {"action" : "stop", "channel" : <integer>} `
  * ` {"action" : "set-now", "channel" : <integer>, "name" : <string>, "value" : <any>} `
  * ` {"action" : "set-queued", "channel" : <integer>, "name" : <string>, "value" : <any>} `
  * ` {"action" : "reset-now", "channel" : <integer>} `
  * ` {"action" : "reset-queued", "channel" : <integer>} `

### Private ###

  * ` {"action" : "get-config", "channel" : <integer>} `

## Extension to Server ##

  * ` {"action" : "play", "channel" : <integer>, "url" : <string>, "deferred" : <integer>, "cache" : true, ["name" : <string>]} `
  * ` {"action" : "deferred-result", "channel" : <integer>, "url" : <string>, "deferred" : <integer>, "filename" : <string>, ["name" : <string>]} `

## Server to Browser Commands ##

  * ` {"action" : "started-say", "channel" : <integer>, ["name" : <string>]} `
  * ` {"action" : "started-play", "channel" : <integer>, ["name" : <string>]} `
  * ` {"action" : "finished-say", "channel" : <integer>, ["name" : <string>]} `
  * ` {"action" : "finished-play", "channel" : <integer>, ["name" : <string>]} `
  * ` {"action" : "started-word", "channel" : <integer>, "location" : <integer>, "length" : <integer>, ["name" : <string>]} `
  * ` {"action" : "set-property", "channel" : <int>, "name" : <string>, "value" : <any>} `
  * ` {"action" : "error", "description" : <string>, "channel" : <integer>, ["name" : <string>], ...} `

### Private ###

  * ` {"action" : "set-config", "channel" : <integer>, "config" : <object>} `