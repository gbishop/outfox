'''
Echo extension JavaScript interface.

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
CLASS = '''\
init: function() {
    // observers of echo respones
    this.observers = [];
    // listen for echo service events
    outfox.addObserver(outfox.utils.bind(this, this._onResponse), 'echo');
    // inform base that extension is ready for use immediately
    outfox._onServiceExtensionReady('echo');
},

/**
 * Ping for an echo.
 *
 * @param text Text to send with the ping.
 */
ping: function(text) {
    if(!text) return;
    var args = {};
    args.text = text;
    args.action = 'ping';
    args.service = 'echo';
    outfox.send(args);
},

/**
 * Adds a listener for all responses from the service with a callback of the 
 * form:
 *
 * function observer(response)
 *
 * where response is the JSON-decoded response object.
 * 
 * @param ob Observer function
 * @return Token to use to unregister this listener
 */
addObserver: function(ob) {
    this.observers.push(ob);
    return ob;
},

/**
 * Removes a listener.
 * 
 * @param token Token returned when registering the listener
 */
removeObserver: function(token) {
    var obs = this.observers;
    for(var i=0; i < obs.length; i++) {
        if(obs[i] == token) {
            // remove the observer from the array
            this.observers = obs.slice(0,i).concat(obs.slice(i+1));
            return;
        }
    }
},

/**
 * Called to handle an arbitrary response from the echo service.
 *
 * @param of Outfox instance
 * @param cmd Command object
 */
_onResponse: function(of, cmd) {
    for(var i=0; i < this.observers.length; i++) {
	    try {
	        this.observers[i](cmd);
	    } catch(e) {
	        // ignore callback exceptions
	    }
    }
}
'''