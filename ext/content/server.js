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
const DELIMITER = '\3';

utils.declare('outfox.ServerProxy', null, {
    constructor: function(name) {
        this.socket = null;
        this.in_str = null;
        this.out_str = null;
	this.observers = {};
	this.in_buff = '';
	this.out_buff = [];
	this.failed = null;

	// encode all outgoing unicode as utf-8
	// decode all incoming to unicode from utf-8
	this.codec = Components.classes["@mozilla.org/intl/scriptableunicodeconverter"].createInstance(Components.interfaces.nsIScriptableUnicodeConverter);
	this.codec.charset = 'utf-8';

        // initialize the socket and launch the server
        var service = this._parseServicesXML(name);
        var port = this._initializeSocket();
        this._initializeProcess(port, service);
    },

    _parseServicesXML: function(name) {
        // build file from path
	var file = utils.buildPath(null, 'platform', 'services.xml');
        // read the XML file
        var istr = Components.classes["@mozilla.org/network/file-input-stream;1"].createInstance(Components.interfaces.nsIFileInputStream);
        istr.init(file, -1, -1)
        var istr_script = Components.classes["@mozilla.org/scriptableinputstream;1"].createInstance(Components.interfaces.nsIScriptableInputStream);
        istr_script.init(istr);
        var count = istr_script.available();
        var xml = istr_script.read(count);
        istr_script.close();
        // DOM parser
        var parser = new DOMParser();
        // parse into document
        var doc = parser.parseFromString(xml);
        // pull the service section
        return doc.getElementById(name);
    },

    shutdown: function() {
        // close connections and port
	this.in_str.close();
	this.out_str.close();
	this.socket.close();
    },

    addObserver: function(page_id, ob) {
	this.observers[page_id] = ob;
	if(this.failed) {
	    this._notify(page_id, this.failed);
	}
    },

    removeObserver: function(page_id) {
	delete this.observers[page_id];
    },

    _initializeSocket: function() {
	while(1) {
	    // pick a random unpriviledged port
	    var port = Math.floor(Math.random() * 64510) + 1025;
	    try {
		// create the server socket component
		this.socket = Components.classes["@mozilla.org/network/server-socket;1"].createInstance(Components.interfaces.nsIServerSocket);
		// intiialize the socket and start it listening
		this.socket.init(port, false, -1);
		this.socket.asyncListen(this);
		break;
	    } catch(e) {
		continue;
            }
	}
        //logit('ServerProxy: opened browser socket', port);
        return port;
    },

    _initializeProcess: function(port, service) {
        var success = false;
        // iterate over all executables until one succeeds
        var execs = service.getElementsByTagName('executable');
        for(var i=0; i<execs.length; i++) {
            var exec = execs[i];
            // build a file for the executable
            var file = utils.buildPath(null, 'platform', exec);
	    try {
                // try to make the file executable
                var chmod = utils.buildPath('/', 'bin', 'chmod');
                utils.runProcess(chmod, ['0755', file.path], true);
            } catch(e) {
                // ignore for now
            }

            // append all arguments after the port number
            var args = [port];
            var nodes = exec.getElementsByTagName('args');
            for(var j=0; j<nodes.length; j++) {
                args.push(nodes[j]);
            }
            
            try {
                // try to launch to process
	        utils.runProcess(file, args, false);
                // return on success to avoid setting the failed var
                return;
            } catch(e) {
                // ignore for now
            }
        }

	// set the failure flag so all future observers receive the error
	this.failed = '{"action" : "service-failed", "description" : "Service ' + name + '" failed to initialize."}';
    },

    _notify: function(page_id, json) {
	if (page_id != '*') {
	    // message for one page
	    try {
		this.observers[page_id](json);
	    } catch(e) {
		//logit('ServerProxy: notify failure', e);
	    }
	} else {
	    // message to all pages can only mean failure, so set the flag
	    this.failed = json;
	    // notify all pages
	    for(var page_id in this.observers) {
		var ob = this.observers[page_id];
		try {
		    ob(json);
		} catch(e) {
		    //logit('ServerProxy: notify all failure', e);
		}
	    }
	}
    },

    send: function(page_id, json) {
	if(this.failed) {
	    // server didn't start, ignore
	}
	if(!this.out_str) {
	    // connection not ready, queue
	    this.out_buff.push([page_id, json]);
	    return;
	}
	// convert unicode to utf-8
	json = this.codec.ConvertFromUnicode(json) + this.codec.Finish();
	
	// include page id and null character delimiter
	var msg = '{"page_id" : '+page_id+', "cmd" : '+json+'}'+DELIMITER;
	var size = msg.length;
	var written = 0;
	// @todo: are we supposed to loop in a callback? delay with a timeout?
	while(written < size) {
	    written += this.out_str.write(msg, msg.length);
	    if(written < size) {
		// avoid doing slice if we don't need it
		msg = msg.slice(written);
	    }
	}
	// make sure we send when a complete command is ready
	this.out_str.flush();
	//logit('ServerProxy: sent message');
    },

    /**
     * Called when an incoming client connects to our listening socket.
     */
    onSocketAccepted: function(socket, transport) {
        if(this.out_str) {
            // don't allow more than one connection to this browser window
            // other browser windows while have their own instances and can
            // start their own connections
            transport.close()
            return;
        }
        
        // @todo: is this how we allow connections from localhost only?
        if(transport.host != '127.0.0.1') {
            transport.close();
            return;
        }

        // open incoming connection
        var stream = transport.openInputStream(0,0,0);
        this.in_str = Components.classes["@mozilla.org/scriptableinputstream;1"].createInstance(Components.interfaces.nsIScriptableInputStream);
        this.in_str.init(stream);
        // set up listener for incoming data
        var pump = Components.classes["@mozilla.org/network/input-stream-pump;1"].createInstance(Components.interfaces.nsIInputStreamPump);
        pump.init(stream, -1, -1, 0, 0, false);
        pump.asyncRead(this,null);

        // open outgoing connection
        this.out_str = transport.openOutputStream(0,0,0);

        //logit('ServerProxy: accepted incoming connection');

	// send any buffered data
	if(this.out_buff.length) {
	    this.out_buff.forEach(function(msg) {
		this.send(msg[0], msg[1]); 
	    }, this);
	}
	this.out_buff = [];
    },

    /**
     * Called when an incoming client disconnects from our listening socket.
     */
    onStopListening: function(socket, status) {
        this.socket.close();
        //logit('ServerProxy: stopped listening');  
    },

    /**
     * Called when the input stream first receives data.
     */
    onStartRequest: function(request, context) {
        //logit('ServerProxy: started request');  
    },

    /**
     * Called when the input stream closes.
     */
    onStopRequest: function(request, context, stop) {
        this.in_str.close();
        this.out_str.close();
        this.in_str = null;
        this.out_str = null;
	this.in_buff = [];
	this.out_buff = [];
        //logit('ServerProxy: stopped request');  
    },

    /**
     * Called when data is available for reading from the input stream.
     */
    onDataAvailable: function(request, context, in_str, offset, count) {
	if(count <= 0) return;
        // use scriptable stream, not the one given
        var data = this.in_str.read(count);
	// split on delimiter
	var segs = data.split(DELIMITER);
	if(segs.length > 1) {
	    // take any leftover data from last receive and prefix it to the
	    // first segment
	    segs[0] = this.in_buff + segs[0];
	    // loop over all commands except the last which can't be complete
	    for(var i=0; i < segs.length-1; i++) {
		var msg = segs[i];
		// convert utf-8 to unicode
		msg = this.codec.ConvertToUnicode(msg) + this.codec.Finish();
                // @todo: could use a hack to avoid decode/encode of json
                var dec = utils.fromJson(msg);
		// dispatch remaining json to observer for the given page id
		this._notify(dec.page_id, utils.toJson(dec.cmd));
	    }
	    // all remaining segment data is prefix for next receive
	    this.in_buff = segs[segs.length-1];
	} else {
	    // save data for later
	    this.in_buff += data;
	}
        //logit('ServerProxy: read data');
    }
});
