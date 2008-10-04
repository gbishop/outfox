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
const GUID = 'outfox@code.google.com';
const ROOT_ID = 'outfox';

/**
 * Manges the creation of page controllers monitoring Outfox in/out queues and
 * server proxies for sending/receiving commands with an external process.
 */
utils.declare('outfox.Factory', null, {
    constructor: function() {
	// integer counter for unique page ids in this window
	this.page_id = 0;
	// dictionary mapping page ids to PageController instances
        this.controllers = {};
	// dictionary mapping page ids to node insertion observer tokens
	this.page_tokens = {};
	// array of document and window observer tokens
        this.tokens = [];
	// dictionary mapping service names to ServerProxy instances
        this.services = {};
	// watch for Firefox window load event
        this.tokens.push(utils.connect(window, 'load', this, 'initialize'));
	//logit('Factory: created');
    },

    /**
     * Called when the Firefox window containing this factory instance loads.
     * 
     * @param event Window load event
     */
    initialize: function(event) {
	// watch for Firefox window unload event
	this.tokens.push(utils.connect(window, 'unload', this, 'shutdown'));
	// start listening for page and tab related events
	var ac = document.getElementById('appcontent');
	this.tokens.push(utils.connect(ac, 'pageshow', this, '_onPageLoad'));
        this.tokens.push(utils.connect(ac, 'pagehide', this, '_onPageUnload'));
	var tabs = gBrowser.tabContainer;
	this.tokens.push(utils.connect(tabs, 'TabClose', this, '_onTabClose',
				       false));
	//logit('Factory: initialized');
    },

    /**
     * Called when the Firefox window containing this factory instance unloads.
     *
     * @param event Window unload event
     */
    shutdown: function(event) {
	// shut down all controllers
	for(var key in this.controllers) {
	    var pc = this.controllers[key];
	    pc.shutdown();
	}
        // unregister all listeners
        this.tokens.forEach(utils.disconnect);
	for(var key in this.page_tokens) {
	    var pt = this.page_tokens[key];
	    utils.disconnect(pt);
	}
        // shutdown all services
        for(var key in this.services) {
            var sv = this.services[key];
            sv.shutdown();
        }
	//logit("Factory: shutdown");
    },

    /**
     * Creates a page controller instance and associates it with the given
     * document.
     *
     * @param page_id ID to assign to the controller
     * @param doc DOM document instance managed by the page
     */
    _createController: function(page_id, doc) {
        // create a controller object
        var pc = new outfox.PageController(page_id, doc, this);
        // store controller in conjunction with the document
        this.controllers[page_id] = pc;
        //logit('Factory: created outfox controller');
    },

    /**
     * Called when a document loads in a tab in the Firefox window.
     *
     * @param event Document load event
     */
    _onPageLoad: function(event) {
	var doc = event.originalTarget;
	if(doc.nodeName == '#document') {
	    // attach the page id to the document so we can unregister listeners
	    // later
	    doc.outfox_page_id = this.page_id;
	    // web page document loaded, look for the outfox node
	    var outfox_node = doc.getElementById(ROOT_ID);
            if(outfox_node) {
		// node exists, create controller
		this._createController(this.page_id, doc);
            } else {
		// monitor node additions to see if it is added later
		var cb = utils.bind(this, this._onNodeInserted, [this.page_id]);
		this.page_tokens[this.page_id] = utils.connect(doc, 'DOMNodeInserted', cb);
		//logit('Factory: created insert watcher');
	    }
	    // increment no matter what so we can track node watcher hook
	    ++this.page_id;
	}
    },
    
    /**
     * Called when a document unloads in a tab in the Firefox window.
     *
     * @param event Document unload event
     */
    _onPageUnload: function(event) {
	var doc = event.originalTarget;
        if(doc.nodeName == '#document') {
	    var page_id = doc.outfox_page_id;
	    // destroy the node watcher for the document
	    var pt = this.page_tokens[page_id];
	    if(pt) {
		utils.disconnect(pt);
		delete this.page_tokens[page_id];
                //logit('Factory: disconnected insert watcher');
	    }
	    // destroy the controller if one exists for the document
	    var pc = this.controllers[page_id];
	    if(pc) {
                pc.shutdown();
                delete this.controllers[page_id];
                //logit('Factory: destroyed outfox controller');
	    }
        }
    },

    /**
     * Called when a tab in the Firefox window closes.
     *
     * @param event Tab close event
     */
    _onTabClose: function(event) {
	var br = gBrowser.getBrowserForTab(event.target);
	var doc = br.contentDocument;
	// spoof a page unload event
	this._onPageUnload({'originalTarget' : doc});
    },

    /**
     * Called when any node is inserted into a document in a tab in the Firefox
     * window.
     *
     * @param page_id ID assigned to the monitored page
     * @param event Node insertion event
     */
    _onNodeInserted: function(page_id, event) {
	var outfox_node = event.originalTarget;
        if(outfox_node.nodeName == 'DIV' && outfox_node.id == ROOT_ID) {
	    // outfox node added after load
	    // remove the node watcher
	    var pt = this.page_tokens[page_id];
	    utils.disconnect(pt);
	    delete this.page_tokens[page_id];
	    //logit('Factory: disconnected insert watcher');
	    // create the controller
	    this._createController(page_id, outfox_node.ownerDocument);
        }
    },

    /**
     * Starts a service if it is not already started. Otherwise, sends the start
     * request along to the running service so that it can account for its use
     * by a new page.
     *
     * @param page_id ID of the page requesting the service start
     * @param service Name of the service to start
     */
    startService: function(page_id, service) {

    },

    /**
     * Stops a service if this is the last page using it. Otherwise, decrements
     * the reference counter on the service.
     *
     * @param page_id ID of the page requesting the service stop
     * @param service Name of the service to stop
     */
    stopService: function(page_id, service) {

    },

    /**
     * Routes a command from a page to a running service.
     * 
     * @param page_id ID of the page requesting the service stop
     * @param cmd Command specifying a service and other data
     */
    send: function(page_id, cmd) {

    }

    // @todo: how to dispatch incoming responses from server proxy?
});

// allow one factory instance per window
var outfox = new outfox.Factory();
