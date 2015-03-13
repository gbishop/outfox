# Why Use Outfox? #

As a web developer, Outfox enables you to access input and output devices beyond what Firefox provides across platforms. Using pure JavaScript, you can potentially synthesize speech; play sounds; get input from joysticks, game pads, and switches; recognize speech; and more. The services you can use are limited only by the Outfox modules the user has installed.

# Using Outfox from JavaScript #

To use Outfox in your web application, you must first include the _outfox.js_ file in your page.

  1. Download a copy of the _outfox.js_ script from http://code.google.com/p/outfox.
  1. Place the file on your web server in a public location.
  1. Include the file in any document that will use Outfox.
    1. ` <script type="text/javascript" src="path/to/outfox.js"></script> `

Next, you must include a JavaScript library with JSON encode and decode functions. For example, you might choose to include the JSON reference implementation.

  1. Download a copy of the _json2.js_ script from http://www.JSON.org/json2.js.
  1. Place the file on your web server in a public location.
  1. Include the file in any document that will use Outfox.
    1. ` <script type="text/javascript" src="path/to/json2.js"></script> `

Now you must initialize Outfox:

  1. Create an element on your page with a well-known ID.
    1. ` <div id="outfox"></div> `
  1. In your page load handler, invoke the ` outfox.init ` method with the element ID and your JSON encode and decode functions.
    1. ` outfox.init("outfox", JSON.stringify, JSON.parse); `

Finally, start the services you wish to use:

  1. Define callbacks for successful service starts and service failures.
    1. ` function onServiceStart(cmd) { // do something on success} `
    1. ` function onServiceFail(cmd) { // do something on failure} `
  1. After invoking ` outfox.init `, use the ` outfox.startService ` method to initialize a service. For example, to start the audio service:
    1. ` outfox.startService('audio').addCallback(onServiceStart).addErrback(onServiceFail); `

If Outfox invokes your success function, you may safely call other service methods:

  1. For example, to speak text using the audio service:
    1. ` outfox.audio.say("Hello out there!") `

View the source for the [Outfox demo page](http://www.cs.unc.edu/Research/assist/outfox/app/test/samples/) for full code samples. See the [JavaScriptAPI](JavaScriptAPI.md) for descriptions of all available methods.