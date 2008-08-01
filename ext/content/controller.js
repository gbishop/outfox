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
    CHANNEL_CLASS : 'channel',

    constructor: function(id, doc, div, proxy) {
        this.id = id;
	this.doc = doc;
        this.div = div;
        this.proxy = proxy;

        // locate or add incoming and outgoing queues
	this.in_queue = this.doc.getElementById(ROOT_ID + '-in');
	this.out_queue = this.doc.getElementById(ROOT_ID + '-out');

	if(this.in_queue == null || this.out_queue == null) {
	    // not a valid outfox node
	    throw new Error('invalid outfox node');
	}

        // watch for additions to the outgoing queues
        this.tokens = [];
        this.tokens.push(utils.connect(this.out_queue, 'DOMNodeInserted',
                                       this, '_onRequest'));

	// register for incoming responses
	this.proxy.addObserver(this.id, utils.bind(this, this._onResponse));

        // send initial request for defaults, voices, etc.
	// this has the desired side effect of creating the default channel and
	// causing a response to be sent to the in-page JS indicating the server
	// is ready
        this.proxy.send(this.id, '{"action" : "get-config"}');

        //logit('PageController: initialized');
    },

    shutdown: function() {
        // unregister all listeners
        this.tokens.forEach(utils.disconnect);
	// stop listening to responses from proxy
	this.proxy.removeObserver(this.id);
        // send a final destroy message for the page
        this.proxy.send(this.id, '{"action" : "shutdown"}');
    },

    _onRequest: function(event) {
	var cmd = event.target;
	if(cmd.nodeName == '#text') {
	    // pull out json encoded command
	    var json = cmd.nodeValue;
	    // destroy request node
	    this.out_queue.removeChild(cmd);
	    // send the json using the proxy
	    this.proxy.send(this.id, json);
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
