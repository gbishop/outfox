/*
 * Copyright (c) 2008 Carolina Computer Assistive Technology
 *
 * Permission to use, copy, modify, and distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 * */
if(!outfox) {
var outfox = {
    /**
     * Initialize outfox. Call once per document frame in which outfox
     * will be used.
     *
     * @param box DOM node which outfox will use for in/out messages
     * @param ready_cb Callback to invoke when outfox is ready for use
     */
    init: function(box, ready_cb) {
	if(typeof box == 'string') {
	    box = document.getElementById(box);
	}
	// create in and out queues
	this.root = document.createElement('div');
	this.root.id = 'outfox';
        // hide the outfox queues
	this.root.style.display = 'none';
	this.in_dom = document.createElement('div');
	this.in_dom.id = 'outfox-in';
	this.out_dom = document.createElement('div');
	this.out_dom.id = 'outfox-out';
	this.root.appendChild(this.in_dom);
	this.root.appendChild(this.out_dom);
	// append all at once so extension can find internal nodes once the 
	// outer one is added
	box.appendChild(this.root);
	// observers for callbacks by channel
	this.observers = {};
        // store callback for ready notification
        this.ready_cb = ready_cb;
        // monitor for incoming events
        this.token = outfox.utils.connect(this.in_dom, 'DOMNodeInserted',
					     this, '_onResponse');
        // configuration by channel
        this.config = {};
        // defaults for a channel when created
        this.defaults = {};
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
        this._send(args);
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
        this._send(args);	
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
        this._send(args);
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
        this._send(args);
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
        this._send(args);
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
        this._send(args);
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
        this._send(args);
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
    
    _onResponse: function(event) {
	var node = event.target;
	var cmd = JSON.parse(node.innerHTML);
        // track whole configuration messages and value changes
	if(cmd.action == 'failed-init') {
	    this._onFailure(cmd);
        } else if(cmd.action == 'set-config') {
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
		    obs[i](this, cmd);
		} catch(e) {
		    // ignore callback exceptions
		}
	    }
        }
        // destroy the DOM node
        this.in_dom.removeChild(node);
    },

    _onSetConfig: function(cmd) {
	// if this is the first config response, it means the server is now
	// initialized and ready for use
        if(this.ready_cb) {
	    // store a copy of the default channel config as the defaults for
	    // all channels; don't store directly because we don't want changes
	    // to the default channel to ruin the property defaults for later
	    // channels
	    for(var key in cmd.config) {
		this.defaults[key] = cmd.config[key];
	    }
            try {
		// tell creator that outfox is ready
                this.ready_cb(this);
            } catch(e) {
                // ignore callback exceptions
            }
            // remove the ready callback
            this.ready_cb = null;
        }
        // store initial configuration for this channel
        this.config[cmd.channel] = cmd.config;
    },

    _onSetProperty: function(cmd) {
        // update local property values when they change server side
	var ch_conf = this.config[cmd.channel];
	if(!ch_conf) {
	    // channel has never been accessed before, use defaults
	    ch_conf = this._copyDefaults();
	    this.config[cmd.channel] = ch_conf;
	}
        ch_conf[cmd.name] = cmd.value;
    },

    _onFailure: function(cmd) {
	this.root.style.display = "block";
	var a = document.createElement('a');
	a.innerHTML = cmd.description;
	a.href = 'http://code.google.com/p/outfox';
	this.root.appendChild(a);
    },

    _copyDefaults: function() {
	var cp = {}
	for(var key in this.defaults) {
	    cp[key] = this.defaults[key];
	}
	return cp;
    },

    _send: function(cmd) {
        var json = JSON.stringify(cmd);
        var node = document.createTextNode(json);
        this.out_dom.appendChild(node);
    }
};

outfox.utils = {
    bind: function(self, func, args) {
	if(typeof args == 'undefined') {
            var f = function() {
		func.apply(self, arguments);
            }
	} else {
            var f = function() {
		var args_inner = Array.prototype.slice.call(arguments);
		func.apply(self, args.concat(args_inner));
            }
	}
        return f;
    },

    connect: function(target, event, self, func, capture) {
        var token = {};
        if(typeof func != 'string' && typeof self == 'function') {
            capture = (func == true);
            token.cb = self;
            target.addEventListener(event, token.cb, capture);
        } else {
            capture = (capture == true)
            token.cb = outfox.utils.bind(self, self[func]);
            target.addEventListener(event, token.cb, capture);
        }
        token.target = target;
        token.event = event;
        token.capture = capture;
        return token;
    },

    disconnect: function(token) {
        token.target.removeEventListener(token.event, token.cb, token.capture);
    }
};
}

/*
    http://www.JSON.org/json2.js
    2008-05-25

    Public Domain.
*/
if (!this.JSON) {

// Create a JSON object only if one does not already exist. We create the
// object in a closure to avoid creating global variables.

    JSON = function () {

        function f(n) {
            // Format integers to have at least two digits.
            return n < 10 ? '0' + n : n;
        }

        Date.prototype.toJSON = function (key) {

            return this.getUTCFullYear()   + '-' +
                 f(this.getUTCMonth() + 1) + '-' +
                 f(this.getUTCDate())      + 'T' +
                 f(this.getUTCHours())     + ':' +
                 f(this.getUTCMinutes())   + ':' +
                 f(this.getUTCSeconds())   + 'Z';
        };

        var cx = /[\u0000\u00ad\u0600-\u0604\u070f\u17b4\u17b5\u200c-\u200f\u2028-\u202f\u2060-\u206f\ufeff\ufff0-\uffff]/g,
            escapeable = /[\\\"\x00-\x1f\x7f-\x9f\u00ad\u0600-\u0604\u070f\u17b4\u17b5\u200c-\u200f\u2028-\u202f\u2060-\u206f\ufeff\ufff0-\uffff]/g,
            gap,
            indent,
            meta = {    // table of character substitutions
                '\b': '\\b',
                '\t': '\\t',
                '\n': '\\n',
                '\f': '\\f',
                '\r': '\\r',
                '"' : '\\"',
                '\\': '\\\\'
            },
            rep;


        function quote(string) {

// If the string contains no control characters, no quote characters, and no
// backslash characters, then we can safely slap some quotes around it.
// Otherwise we must also replace the offending characters with safe escape
// sequences.

            escapeable.lastIndex = 0;
            return escapeable.test(string) ?
                '"' + string.replace(escapeable, function (a) {
                    var c = meta[a];
                    if (typeof c === 'string') {
                        return c;
                    }
                    return '\\u' + ('0000' +
                            (+(a.charCodeAt(0))).toString(16)).slice(-4);
                }) + '"' :
                '"' + string + '"';
        }


        function str(key, holder) {

// Produce a string from holder[key].

            var i,          // The loop counter.
                k,          // The member key.
                v,          // The member value.
                length,
                mind = gap,
                partial,
                value = holder[key];

// If the value has a toJSON method, call it to obtain a replacement value.

            if (value && typeof value === 'object' &&
                    typeof value.toJSON === 'function') {
                value = value.toJSON(key);
            }

// If we were called with a replacer function, then call the replacer to
// obtain a replacement value.

            if (typeof rep === 'function') {
                value = rep.call(holder, key, value);
            }

// What happens next depends on the value's type.

            switch (typeof value) {
            case 'string':
                return quote(value);

            case 'number':

// JSON numbers must be finite. Encode non-finite numbers as null.

                return isFinite(value) ? String(value) : 'null';

            case 'boolean':
            case 'null':

// If the value is a boolean or null, convert it to a string. Note:
// typeof null does not produce 'null'. The case is included here in
// the remote chance that this gets fixed someday.

                return String(value);

// If the type is 'object', we might be dealing with an object or an array or
// null.

            case 'object':

// Due to a specification blunder in ECMAScript, typeof null is 'object',
// so watch out for that case.

                if (!value) {
                    return 'null';
                }

// Make an array to hold the partial results of stringifying this object value.

                gap += indent;
                partial = [];

// If the object has a dontEnum length property, we'll treat it as an array.

                if (typeof value.length === 'number' &&
                        !(value.propertyIsEnumerable('length'))) {

// The object is an array. Stringify every element. Use null as a placeholder
// for non-JSON values.

                    length = value.length;
                    for (i = 0; i < length; i += 1) {
                        partial[i] = str(i, value) || 'null';
                    }

// Join all of the elements together, separated with commas, and wrap them in
// brackets.

                    v = partial.length === 0 ? '[]' :
                        gap ? '[\n' + gap +
                                partial.join(',\n' + gap) + '\n' +
                                    mind + ']' :
                              '[' + partial.join(',') + ']';
                    gap = mind;
                    return v;
                }

// If the replacer is an array, use it to select the members to be stringified.

                if (rep && typeof rep === 'object') {
                    length = rep.length;
                    for (i = 0; i < length; i += 1) {
                        k = rep[i];
                        if (typeof k === 'string') {
                            v = str(k, value, rep);
                            if (v) {
                                partial.push(quote(k) + (gap ? ': ' : ':') + v);
                            }
                        }
                    }
                } else {

// Otherwise, iterate through all of the keys in the object.

                    for (k in value) {
                        if (Object.hasOwnProperty.call(value, k)) {
                            v = str(k, value, rep);
                            if (v) {
                                partial.push(quote(k) + (gap ? ': ' : ':') + v);
                            }
                        }
                    }
                }

// Join all of the member texts together, separated with commas,
// and wrap them in braces.

                v = partial.length === 0 ? '{}' :
                    gap ? '{\n' + gap + partial.join(',\n' + gap) + '\n' +
                            mind + '}' : '{' + partial.join(',') + '}';
                gap = mind;
                return v;
            }
        }

// Return the JSON object containing the stringify and parse methods.

        return {
            stringify: function (value, replacer, space) {

// The stringify method takes a value and an optional replacer, and an optional
// space parameter, and returns a JSON text. The replacer can be a function
// that can replace values, or an array of strings that will select the keys.
// A default replacer method can be provided. Use of the space parameter can
// produce text that is more easily readable.

                var i;
                gap = '';
                indent = '';

// If the space parameter is a number, make an indent string containing that
// many spaces.

                if (typeof space === 'number') {
                    for (i = 0; i < space; i += 1) {
                        indent += ' ';
                    }

// If the space parameter is a string, it will be used as the indent string.

                } else if (typeof space === 'string') {
                    indent = space;
                }

// If there is a replacer, it must be a function or an array.
// Otherwise, throw an error.

                rep = replacer;
                if (replacer && typeof replacer !== 'function' &&
                        (typeof replacer !== 'object' ||
                         typeof replacer.length !== 'number')) {
                    throw new Error('JSON.stringify');
                }

// Make a fake root object containing our value under the key of ''.
// Return the result of stringifying the value.

                return str('', {'': value});
            },


            parse: function (text, reviver) {

// The parse method takes a text and an optional reviver function, and returns
// a JavaScript value if the text is a valid JSON text.

                var j;

                function walk(holder, key) {

// The walk method is used to recursively walk the resulting structure so
// that modifications can be made.

                    var k, v, value = holder[key];
                    if (value && typeof value === 'object') {
                        for (k in value) {
                            if (Object.hasOwnProperty.call(value, k)) {
                                v = walk(value, k);
                                if (v !== undefined) {
                                    value[k] = v;
                                } else {
                                    delete value[k];
                                }
                            }
                        }
                    }
                    return reviver.call(holder, key, value);
                }


// Parsing happens in four stages. In the first stage, we replace certain
// Unicode characters with escape sequences. JavaScript handles many characters
// incorrectly, either silently deleting them, or treating them as line endings.

                cx.lastIndex = 0;
                if (cx.test(text)) {
                    text = text.replace(cx, function (a) {
                        return '\\u' + ('0000' +
                                (+(a.charCodeAt(0))).toString(16)).slice(-4);
                    });
                }

// In the second stage, we run the text against regular expressions that look
// for non-JSON patterns. We are especially concerned with '()' and 'new'
// because they can cause invocation, and '=' because it can cause mutation.
// But just to be safe, we want to reject all unexpected forms.

// We split the second stage into 4 regexp operations in order to work around
// crippling inefficiencies in IE's and Safari's regexp engines. First we
// replace the JSON backslash pairs with '@' (a non-JSON character). Second, we
// replace all simple value tokens with ']' characters. Third, we delete all
// open brackets that follow a colon or comma or that begin the text. Finally,
// we look to see that the remaining characters are only whitespace or ']' or
// ',' or ':' or '{' or '}'. If that is so, then the text is safe for eval.

                if (/^[\],:{}\s]*$/.
test(text.replace(/\\(?:["\\\/bfnrt]|u[0-9a-fA-F]{4})/g, '@').
replace(/"[^"\\\n\r]*"|true|false|null|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?/g, ']').
replace(/(?:^|:|,)(?:\s*\[)+/g, ''))) {

// In the third stage we use the eval function to compile the text into a
// JavaScript structure. The '{' operator is subject to a syntactic ambiguity
// in JavaScript: it can begin a block or an object literal. We wrap the text
// in parens to eliminate the ambiguity.

                    j = eval('(' + text + ')');

// In the optional fourth stage, we recursively walk the new structure, passing
// each name/value pair to a reviver function for possible transformation.

                    return typeof reviver === 'function' ?
                        walk({'': j}, '') : j;
                }

// If the text is not JSON parseable, then a SyntaxError is thrown.

                throw new SyntaxError('JSON.parse');
            }
        };
    }();
}
