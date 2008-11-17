/*
Audio extension JavaScript interface.

Copyright (c) 2008 Carolina Computer Assistive Technology

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
*/
init: function() {
    // observers of audio channel messages
    this.observers = {};
    // configuration by channel
    this.config = {};
    // defaults no default until they come back from the server
    this.defaults = null;
    // listen for audio service events
    outfox.addObserver(outfox.utils.bind(this, this._onResponse), 'audio');
    // send request for default config
    var cmd = {'action' : 'get-config', 'channel' : 0};
    outfox.send(cmd);
},

/**
 * Speak text.
 *
 * @param text Text to speak
 * @param channel Channel to use to speak (defaults to 0)
 * @param name Name to include with any callbacks generated while speaking
 *   (defaults to no name)
 */
say: function(text, channel, name) {
    if(!text) return;
    var args = {};
    args.channel = channel || 0;
    args.text = text;
    if(typeof name != 'undefined')
        args.name = name;
    args.action = 'say';
    outfox.send(args);
},

/**
 * Play a sound at a relative or absolute URL.
 *
 * @param url URL relative to the document invoking this method
 * @param channel Channel to use to play (defaults to 0)
 * @param name Name to include with any callbacks generated while playing
 *   (defaults to no name)
 */
play: function(url, channel, name) {
    if(!url) return;
    var args = {};
    args.channel = channel || 0;
    args.url = url;
    if(typeof name != 'undefined')
        args.name = name;
    args.action = 'play';
    outfox.send(args);	
},

/**
 * Stop all output on a channel immediately.
 *
 * @param channel Channel to stop (defaults to 0)
 */
stop: function(channel) {
    var args = {};
    args.channel = channel || 0;        
    args.action = 'stop';
    outfox.send(args);
},

/**
 * Set a property on a channel immediately
 *
 * @param name Name of the property to set
 * @param value Value to set on the property
 * @param channel Channel to modify (defaults to 0)
 */
setPropertyNow: function(name, value, channel) {
    if(!name) return;
    var args = {};
    args.channel = channel || 0;
    args.name = name;
    args.value = value || '';
    args.action = 'set-now';
    outfox.send(args);
    // since the value will be applied immediately, update the local
    // property value too
    var ch_conf = this.config[channel];
    if(!ch_conf) {
        // channel has never been accessed before, use defaults
        ch_conf = this._copyDefaults();
        this.config[channel] = ch_conf;
    }
    ch_conf[name] = value;
},

/**
 * Set a property on a channel when this command is processed in the queue.
 *
 * @param name Name of the property to set
 * @param value Value to set on the property
 * @param channel Channel to modify (defaults to 0)
 */
setProperty: function(name, value, channel) {
    if(!name) return;
    var args = {};
    args.channel = channel || 0;
    args.name = name;
    args.value = value || '';
    args.action = 'set-queued';
    outfox.send(args);
    // do not update local until the server gives notice that the value
    // has actually changed
},

/**
 * Get the value of a property on a channel immediately. If the channel
 * has not been accessed yet, sets it to the defaults and retrieves the
 * requested value.
 *
 * @param name Name of the property to get
 * @param channel Channel to modify (defaults to 0)
 */
getProperty: function(name, channel) {
    // fetch from local store
    channel = channel || 0;
    var ch_conf = this.config[channel];
    if(!ch_conf) {
        // channel has never been accessed before, use defaults
        ch_conf = this._copyDefaults();
        this.config[channel] = ch_conf;
    }
    // return value for property name
    return ch_conf[name];
},

/**
 * Reset the channel properties to their defaults immediately.
 *
 * @param channel Channel to modify (defaults to 0)
 */
resetNow: function(channel) {
    channel = channel || 0;
    var args = {};
    args.action = 'reset-now';
    outfox.send(args);
},

/**
 * Reset the channel properties to their defaults when this command is
 * processed in the queue.
 *
 * @param channel Channel to modify (defaults to 0)
 */
reset: function(channel) {
    channel = channel || 0;
    var args = {};
    args.action = 'reset-queued';
    outfox.send(args);
},

/**
 * Adds a listener for events in a channel. The listener signature should be
 *
 * function observer(outfox, cmd)
 *
 * where outfox is the outfox object and cmd is an object with all of the
 * callback data as properties.
 * 
 * @param ob Observer function
 * @param channel Channel to observe (defaults to 0)
 * @return Token to use to unregister this listener
 */
addObserver: function(ob, channel) {
    channel = channel || 0;
    if(typeof this.observers[channel] == 'undefined') {
        this.observers[channel] = [];
    }
    this.observers[channel].push(ob);
    return [channel, ob];
},

/**
 * Removes a listener from a channel.
 * 
 * @param token Token returned when registering the listener
 */
removeObserver: function(token) {
    var obs = this.observers[token[0]];
    for(var i=0; i < obs.length; i++) {
        if(obs[i] == token[1]) {
            // remove the observer from the array
            this.observers[token[0]] = obs.slice(0,i).concat(obs.slice(i+1));
        }
    }
},

/**
 * Called to handle an arbitrary response from the server.
 *
 * @param of Outfox instance
 * @param cmd Command object
 */
_onResponse: function(of, cmd) {
    // track whole configuration messages and value changes
    if(cmd.action == 'set-config') {
        this._onSetConfig(cmd);
    } else if(cmd.action == 'set-property') {
        this._onSetProperty(cmd);
    }
    // let observers know about the message
    // handling last means any observer registered in the ready callback
    // will also be notified of initial config
    var obs = this.observers[cmd.channel];
    if(typeof obs != 'undefined') {
        for(var i=0; i < obs.length; i++) {
        	try {
        	    obs[i](cmd);
        	} catch(e) {
        	    // ignore callback exceptions
        	}
        }
    }
},

/**
 * Called to store a client copy of channel properties held by the server.
 * Stores the first set received as the default for all future channels.
 *
 * @param cmd Command with action set-config 
 */
_onSetConfig: function(cmd) {
    // store initial configuration for this channel
    this.config[cmd.channel] = cmd.config;
    if(this.defaults == null) {
        // first config response, make a copy as default
        for(var key in cmd.config) {
	        this.defaults[key] = cmd.config[key];
        }
        // inform base that extension is ready for use
        outfox._onServiceExtensionReady('audio');
    }
},

/**
 * Called to update local property values when they change server side.
 * 
 * @param cmd Command with action set-property
 */ 
_onSetProperty: function(cmd) {
    var ch_conf = this.config[cmd.channel];
    if(!ch_conf) {
        // channel has never been accessed before, use defaults
        ch_conf = this._copyDefaults();
        this.config[cmd.channel] = ch_conf;
    }
    ch_conf[cmd.name] = cmd.value;
},

/**
 * Makes an independent copy of the channel defaults for use by a channel.
 */
_copyDefaults: function() {
    var cp = {}
    for(var key in this.defaults) {
        cp[key] = this.defaults[key];
    }
    return cp;
},
