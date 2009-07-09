'''
Audio extension JavaScript interface.

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
    // observers of audio channel messages
    this.observers = {};
    // configuration by channel
    this.config = {};
    // defaults no default until they come back from the server
    this.defaults = null;
    // listen for audio service events
    outfox.addObserver(outfox.utils.bind(this, this._onResponse), 'audio');
    // send request for default config
    var cmd = {};
    cmd.action = 'get-config';
    cmd.channel = 0;
    this.send(cmd);
},

/**
 * Sends a command with service attribute set to audio.
 *
 * @param cmd Command object
 */
send: function(cmd) {
    cmd.service = 'audio';
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
    this.send(args);
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
    url = this._relToAbsUrl(url);
    var args = {};
    args.channel = channel || 0;
    args.url = url;
    if(typeof name != 'undefined')
        args.name = name;
    args.action = 'play';
    args.cache = true;
    this.send(args);
},

/**
 * Stream a sound at a relative or absolute URL.
 *
 * @param url URL relative to the document invoking this method
 * @param channel Channel to use to play (defaults to 0)
 * @param name Name to include with any callbacks generated while playing
 *   (defaults to no name)
 */
stream: function(url, channel, name) {
    if(!url) return;
    url = this._relToAbsUrl(url);
    var args = {};
    args.channel = channel || 0;
    args.url = url;
    if(typeof name != 'undefined')
        args.name = name;
    args.action = 'play';
    args.cache = false;
    this.send(args);	
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
    this.send(args);
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
    this.send(args);
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
    this.send(args);
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
    this.send(args);
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
    this.send(args);
},

/**
 * Fetches all of the given urls so that they are in the local cache when
 * later used. Useful for ensuring all sounds are local before playing them.
 * Bad URLs and errors fetching data are ignored.
 *
 * @param urls Array of URLs
 * @return Deferred invoked when all requests complete, successfully or not
 */
precache: function(urls) {
    var done = urls.length;
    var def = new outfox.Deferred();
    for(var i=0; i < urls.length; i++) {
        var url = urls[i];
        var req = new XMLHttpRequest();
        try {
            req.open('GET', url, true);
        } catch(e) {
            // ignore bad urls to start
            --done;
            continue;
        }
        req.onreadystatechange = function(event) {
            if(event.target.readyState == 4) {
                --done;
                if(done == 0) def.callback(true);
            }
        };
        try {
            req.send(null);
        } catch(e) {
            // ignore bad urls to start
            --done;            
        }
    }
    return def;
},

/**
 * Adds a listener for events in a channel. The listener signature should be
 *
 * function observer(audio, cmd)
 *
 * where outfox is the outfox.audio object and cmd is an object with all of the
 * callback data as properties.
 * 
 * @param ob Observer function
 * @param channel Integer channel to observe (defaults to 0)
 * @param actions Array of action strings to observe (defaults to all)
 * @return Token to use to unregister this listener
 */
addObserver: function(ob, channel, actions) {
    channel = channel || 0;
    var packet = {};
    packet.ob = ob;
    packet.actions = actions;
    if(typeof this.observers[channel] == 'undefined') {
        this.observers[channel] = [];
    }
    this.observers[channel].push(packet);
    return [channel, packet];
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
 * Called to adjust a relative sound URL so that it is absolute.
 *
 * @param url Relative or absolute URL
 * @return Absolute URL
 */
_relToAbsUrl: function(url) {
    if(url.indexOf('http://') == 0 || url.indexOf('https://') == 0) {
        // abs url
        return url;
    } else if(url.indexOf('/') == 0) {
        // relative to server root
        return window.location.protocol + '//' + window.location.host + url;
    } else {
        // relative to current path
        var path = window.location.pathname;
        if(path.lastIndexOf('/') != path.length-1) {
            // remove filename from path
            path = path.split('/').slice(0, -1).join('/') + '/';
        }
        return window.location.protocol + '//' + window.location.host + path + url;
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
            var packet = obs[i];
            if(typeof(packet.actions) == 'undefined' || 
                packet.actions.indexOf(cmd.action) != -1) {
                // observer wants this action
        	    try {
        	        packet.ob(this, cmd);
        	    } catch(e) {
        	        // ignore callback exceptions
        	    }
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
        this.defaults = {};
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
}
'''