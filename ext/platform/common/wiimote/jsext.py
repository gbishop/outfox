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
    outfox.addObserver(outfox.utils.bind(this, this._onResponse), 'wiimote');
    // inform base that extension is ready for use immediately
    outfox._onServiceExtensionReady('wiimote');
},

/**
 * Connect to the wiimote at the given address.
 *
 * @param wm Address of the wiimote to connect or 'any' to connect to any available wiimote.
 */
connect: function(address) {
    var args = {};
    args.action = 'connect';
    args.service = 'wiimote';
    args.address = address;
    outfox.send(args);
},

/**
 * Set a property on the wiimote.
 *
 * @param wm ID of the wiimote to control
 * @param name Name of the property to set
 * @param value Value to set on the property
 */
setProperty: function(wm, name, value) {
    var args = {};
    args.action = 'set-property';
    args.service = 'wiimote';
    args.wm = wm;
    args.name = name;
    args.value = value;
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
 * @param actions Array of action strings to observe (defaults to all)
 * @return Token to use to unregister this listener
 */
addObserver: function(actions, ob) {
    var packet = {};
    packet.ob = ob;
    if(typeof(actions) == 'string') actions = [ actions ];
    packet.actions = actions;
    this.observers.push(packet);
    return packet;
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
 * Called to handle an arbitrary response from the wiimote service.
 *
 * @param of Outfox instance
 * @param cmd Command object
 */
_onResponse: function(of, cmd) {
    for(var i=0; i < this.observers.length; i++) {
            var packet = this.observers[i];
            if(typeof(packet.actions) == 'undefined' ||
                packet.actions.indexOf(cmd.action) != -1) {
                // observer wants this action
	           try {
	                packet.ob(cmd);
	           } catch(e) {
                        console.debug(e);
	                // ignore callback exceptions
	           }
            }
    }
}
'''
