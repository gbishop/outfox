# Components #

Outfox consists of three major components:

  1. _Client_: JavaScript interface used by Web applications in a browser tab to invoke Outfox services. Delivers messages sent by a server to observers.
  1. _Extension_: XUL and JavaScript overlay that monitors Firefox tabs and windows for the presence of the Outfox client. Establishes communication between the client and server via a persistent local socket.
  1. _Server_: External process that manages a service on a per page basis. Initializes a service on request, delivers messages from the client, sends responses to the client, and terminates a service when all pages using it unload.

# Communication #

A Web application initiates use of Outfox by embedding the client script in a document frame and invoking an initialize method. The Web application is then free to start, stop, send commands to, and receive responses from services at will. Once a service starts, the Outfox client exposes a JavaScript interface with methods for communicating with the server-side of that service. These JavaScript methods encode commands in JSON format and insert them as DOM nodes into a well-known "queue" node on the Web page.

The extension page controller observes the DOM node insertion and extracts the JSON command. The page controller adds its unique page ID to the JSON. It then invokes a method on the extension server proxy to transmit the JSON to the external server-side process for the service. The proxy sends the JSON message with a well-known delimiter to the process via a socket opened when the service started.

The server socket manager collects segments of the JSON messages. When a delimiter is seen, the socket manager sends a complete JSON message to the server controller. The controller decodes the JSON to a dictionary object and sends it to other controllers designed specifically for the service invoked. Typically, a page controller receives the dictionary next and then dispatches it to sub-controllers for specific platforms.

The server-side portion of a service can send responses to its client-side in a reverse process. When a response reaches the Outfox JavaScript client, the core client code delivers it to callbacks registered by a service interface.

The messages supported are defined in detail on the [JSONProtocol](JSONProtocol.md) page.

![http://outfox.googlecode.com/svn/wiki/images/overview.png](http://outfox.googlecode.com/svn/wiki/images/overview.png)