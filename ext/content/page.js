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
utils.declare('outfox.PageController', null, {
    constructor: function(id, doc, factory) {
        this.id = id;
	this.doc = doc;
	this.factory = factory;

	// create cache session
	this.cache = new outfox.CacheController();

        // locate or add incoming and outgoing queues
	this.in_queue = this.doc.getElementById(ROOT_ID + '-in');
	this.out_queue = this.doc.getElementById(ROOT_ID + '-out');

	if(this.in_queue == null || this.out_queue == null) {
	    // not a valid outfox node
	    throw new Error('invalid outfox node');
	}

        // watch for additions to the outgoing queuesb
        this.tokens = [];
        this.tokens.push(utils.connect(this.out_queue, 'DOMNodeInserted',
                                       this, '_onRequest'));

	// run through everything in the outgoing queue and process it 
	// immediately

	// register for incoming responses
	//this.proxy.addObserver(this.id, utils.bind(this, this._onResponse));

        logit('PageController: initialized');
    },

    shutdown: function() {
        // unregister all listeners
        this.tokens.forEach(utils.disconnect);
	// stop listening to responses from proxy
	//this.proxy.removeObserver(this.id);
    },

    _onRequest: function(event) {
	var node = event.target;
	if(node.nodeName == '#text') {
	    // pull out json encoded command
	    var json = node.nodeValue;
	    var cmd = utils.fromJson(json);

	    if(cmd.action == 'start-service') {
		// service start request
		this.factory.startService(this.id, cmd);
	    } else if(cmd.action == 'stop-service') {
		// service stop request
		this.factory.stopService(this.id, cmd);
	    } else if(cmd.url) {
		// request containing a URL that we might be able to cache
		var fn;
		// check if url is cached
		try {
		    fn = this.cache.getLocalFilename(cmd.url);
		} catch(e) {
		    // any exception here means the file isn't cacheable
		    // leave fn undefined
		    logit('cache entry exists, but file not on disk');
		}
		if(fn === null) {
		    // define a callback for when the prefetch completes and
		    // the cache entry is opened for filename access
		    var self = this;
		    var obs = function(reqid, filename) {
			// change the action to indicate a deferred result
			// which can be paired with the original based on the
			// deferred request id
			cmd.action = 'deferred-result';
			if(filename) {
			    // attach the filename, if it exists
			    cmd.filename = filename;
			}
			// send the command to the proper service
			self.factory.send(self.id, cmd);
		    }
		    // prefetch url
		    var reqid = this.cache.fetch(cmd.url, obs);
		    // mark command as deferred for now
		    cmd.deferred = reqid;
		} else if(fn != undefined){
		    // make the command with the local cached copy filename
		    // in case the external server can make use of it instead
		    cmd.filename = fn;
		}
	    }

	    // destroy request node
	    this.out_queue.removeChild(node);
	    // send the json using the proxy
	    this.factory.send(this.id, cmd);
	}
    },

    _onResponse: function(json) {
        // add a node with the incoming json
	var cmd = this.doc.createElement('div');
        var tn = this.doc.createTextNode(json);
	cmd.appendChild(tn);
	this.in_queue.appendChild(cmd);
    }
});
