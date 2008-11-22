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

/**
 * Manages a single socket connection to an external service process.
 */
utils.declare('outfox.ServerProxy', null, {
    /**
     * Initiates the service connection.
     *
     * @param name String name of the service to be launched by this proxy
     */
    constructor: function(name) {
        // listening socket for service connections
        this.socket = null;
        // incoming stream from external service
        this.in_str = null;
        // outgoing stream to external service
        this.out_str = null;
        // dictionary mapping page ids to PageControllers observing the service
        // id * is reserved for the creating factory
        this.observers = {};
        // number of observers (a reference count)
        this.observer_count = 0;
        // incoming stream buffer
        this.in_buff = '';
        // outgoing stream buffer
        this.out_buff = [];
        // string service name
        this.name = name;

        // encode all outgoing unicode as utf-8
        // decode all incoming to unicode from utf-8
        this.codec = Components.classes["@mozilla.org/intl/scriptableunicodeconverter"].createInstance(Components.interfaces.nsIScriptableUnicodeConverter);
        this.codec.charset = 'utf-8';

        // let all exceptions during startup bubble to the caller

        // parse the services document
        var service = this._parseServicesXML(name);
        // open a listening socket
        var port = this._initializeSocket(10);
        // launch the service process
        this._initializeProcess(port, service);
    },

    /**
     * Closes the streams and socket.
     */
    shutdown: function() {
        this.in_str.close();
        this.out_str.close();
        this.socket.close();
        this.in_str = null;
        this.out_str = null;
        this.socket = null;
        this.out_buff = [];
        this.in_buff = '';
        this.observers = [];
        logit('ServerProxy: shutdown');
    },

    /**
     * Adds an observer for responses from the service. One allowed per page.
     * Returns the total number of observers for this service.
     *
     * @param page_id Page id of the observer
     * @param ob Observer function
     * @return Number of registered observers
     */
    addObserver: function(page_id, ob) {
        this.observers[page_id] = ob;
        this.observer_count += 1;
        return this.observer_count;
    },

    /**
     * Removes an observer from the service.
     *
     * @param page_id Page id of the observer
     */    
    removeObserver: function(page_id) {
        delete this.observers[page_id];
        this.observer_count -= 1;
        return this.observer_count;
    },
    
    /**
     * Builds a service failed response object, JSON encodes it, and returns 
     * it.
     *
     * @param description Description of the failure
     * @return Failure response object
     */
    _buildFailure: function(description) {
        var resp = {};
        resp.action = 'failed-service';
        resp.description = description;
        resp.service = this.name;
        return utils.toJson(resp);
    },
    
    /**
     * Reads the services XML file to find information about the service
     * managed by this proxy. Throws exceptions if the file is not readable,
     * parseable, or does not contain info about the named service.
     *
     * @param name Name of the service
     */
    _parseServicesXML: function(name) {
        // build file from path
        var file = utils.buildPath(null, 'platform', 'services.xml');
        // read the entire XML file
        try {
            var istr = Components.classes["@mozilla.org/network/file-input-stream;1"].createInstance(Components.interfaces.nsIFileInputStream);
            istr.init(file, 0x01, 444, undefined);
            var istr_script = Components.classes["@mozilla.org/scriptableinputstream;1"].createInstance(Components.interfaces.nsIScriptableInputStream);
            istr_script.init(istr);
            var count = istr_script.available();
            var xml = istr_script.read(count);
            istr_script.close();
        } catch (e) {
            var desc = 'Could not read services XML.';
            throw new Error(this._buildFailure(desc));
        }

        try {
            // DOM parser
            var parser = new DOMParser();
            // parse into document
            var doc = parser.parseFromString(xml, 'text/xml');
        } catch(e) {
            var desc = 'Could not parse services DOM.';
            throw new Error(this._buildFailure(desc));
        }
        
        // pull all services sections; doc.getElementById not implemented
        // for generic xml:id ...
        var service = null;
        var elems = doc.getElementsByTagName('service');
        for(var i=0; i < elems.length; i++) {
            var elem = elems[i];
            if(elem.getAttribute('id') == name) {
                service = elem;
                break;
            }
        };
        
        if(service == null) {
            var desc = 'Unknown service.';
            throw new Error(this._buildFailure(desc));
        }
        return service;
    },

    /**
     * Initializes a listening socket. Returns the listening port number.
     * Throws an exception if a free port is not found after the given number
     * of tries.
     * 
     * @param tries Number of times to try finding an open port before failure
     * @return Integer port number
     */
    _initializeSocket: function(tries) {
        while(tries > 0) {
            // pick a random unpriviledged port
            var port = Math.floor(Math.random() * 64510) + 1025;
            try {
                // create the server socket component
                this.socket = Components.classes["@mozilla.org/network/server-socket;1"].createInstance(Components.interfaces.nsIServerSocket);
                // intiialize the socket and start it listening
                this.socket.init(port, false, -1);
                this.socket.asyncListen(this);
                return port;
            } catch(e) {
                // try again
                tries -= 1;
                continue;
            }
        }
        // failed to open a port
        var desc = 'Could not find free port.';
        throw new Error(this._buildFailure(desc));
    },

    /**
     * Attempts to launch the service process. Throws an exception if the
     * process does not launch.
     *
     * @param port Port number opened for service connections
     * @param service Service DOM from the services XML file
     */
    _initializeProcess: function(port, service) {
        var success = false;
        // iterate over all executables until one succeeds
        var execs = service.getElementsByTagName('executable');
        for(var i=0; i<execs.length; i++) {
            var exec = execs[i];
            // build a file for the executable
            var file = utils.buildPath(null, 'platform', exec.getAttribute('path'));
            try {
                // try to make the file executable
                var chmod = utils.buildPath('/', 'bin', 'chmod');
                utils.runProcess(chmod, ['0755', file.path], true);
            } catch(e) {
                // ignore for now
            }

            // append all arguments after the port number
            var args = [port];
            var nodes = exec.getElementsByTagName('arg');
            for(var j=0; j<nodes.length; j++) {
                args.push(nodes[j].getAttribute('value'));
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
        
        // indicate failure
        var desc = 'Could not launch service process.'
        throw new Error(this._buildFailure(desc));
    },

    /**
     * Notifies observer(s) of a response in JSON format.
     *
     * @param page_id ID of the page to receive the response
     * @param json Response from service
     */
    _notify: function(page_id, json) {
        if (page_id != '*') {
            // message for one observer
            try {
                this.observers[page_id](json);
            } catch(e) {
                logit('ServerProxy: notify failure', e);
            }
        } else {
            // notify all observers
            for(var page_id in this.observers) {
                var ob = this.observers[page_id];
                try {
                    ob(json);
                } catch(e) {
                    logit('ServerProxy: notify all failure', e);
                }
            }
        }
    },

    /**
     * Sends a command from a page to an external service.
     *
     * @param page_id ID of the page sending the command
     * @param json Command for service
     */
    send: function(page_id, json) {
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
        logit('ServerProxy: sent message');
    },

    /**
     * Called when an incoming client connects to the listening socket.
     * 
     * @param socket Socket object
     * @param transport Transport object
     */
    onSocketAccepted: function(socket, transport) {
        if(this.out_str) {
            // don't allow more than one connection to this browser window
            // other browser windows while have their own instances and can
            // start their own connections
            transport.close()
            return;
        }

        if(transport.host != '127.0.0.1') {
            // abort if the connection isn't from localhost
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
        pump.asyncRead(this, null);

        // open outgoing connection
        this.out_str = transport.openOutputStream(0,0,0);

        logit('ServerProxy: accepted incoming connection');

        // send any buffered data
        if(this.out_buff.length) {
            this.out_buff.forEach(function(msg) {
                this.send(msg[0], msg[1]); 
            }, this);
        }
        // empty the output buffer
        this.out_buff = [];
    },

    /**
    * Called when an incoming client disconnects from our listening socket.
    *
    * @param socket Socket object
    * @param status Status of the socket
    */
    onStopListening: function(socket, status) {
        // if we have observers, then we didn't initiate this stop so
        // close the socket and notify observers of an unexpected failure
        this.socket.close();
        var desc = 'Unexpected service failure.';
        this._notify('*', this._buildFailure(desc));
        logit('ServerProxy: stopped listening');  
    },

    /**
    * Called when the input stream first receives data.
    *
    * @param request Request object
    * @param context Context of the request
    */
    onStartRequest: function(request, context) {
        logit('ServerProxy: started request');  
    },

    /**
    * Called when the input stream closes.
    *
    * @param request Request object
    * @param context Context of the request
    */
    onStopRequest: function(request, context, stop) {
        // @todo: notify someone?
        this.in_str.close();
        this.out_str.close();
        this.in_str = null;
        this.out_str = null;
        this.in_buff = [];
        this.out_buff = [];
        logit('ServerProxy: stopped request');  
    },

    /**
    * Called when data is available for reading from the input stream.
    *
    * @param request Request object
    * @param context Context of the request
    * @param in_str Incoming stream (C not JS, do not use)
    * @param offset Offset of waiting bytes from zero
    * @param count Number of waiting bytes
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
        logit('ServerProxy: read data');
    }
});
