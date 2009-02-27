/*
* Copyright (c) 2008, 2009 Carolina Computer Assistive Technology
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
const ROOT_ID = 'outfox@code.google.com';
const VERSION = '0.3.2';

/**
* Manages the creation of page controllers monitoring Outfox in/out queues and
* server proxies for sending/receiving commands with an external process.
*/
utils.declare('outfox.Factory', null, {
    constructor: function() {
        // integer counter for unique page ids in this window
        this.page_id = 0;
        // dictionary mapping page ids to node insertion observer tokens
        this.page_tokens = {};
        // array of document and window observer tokens
        this.tokens = [];
        // dictionary mapping service names to ServerProxy instances
        this.services = {};
        // dictionary mapping page ids to PageController instances
        this.controllers = {};
        // watch for Firefox window load event
        this.tokens.push(utils.connect(window, 'load', this, 'initialize'));
        logit('Factory: created');
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
        logit('Factory: initialized');
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
        logit("Factory: shutdown");
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
        logit('Factory: created page controller');
    },

    /**
    * Called when a document loads in a tab in the Firefox window.
    *
    * @param event Document load event
    */
    _onPageLoad: function(event) {
        logit('Factory: page load detected');
        var doc = event.originalTarget;
        if(doc.nodeName == '#document') {
            logit('Factory: page processing started');
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
                var cb = utils.bind(this, this._onNodeInserted, 
                    [this.page_id]);
                this.page_tokens[this.page_id] = utils.connect(doc, 
                    'DOMNodeInserted', cb);
                logit('Factory: created insert watcher');
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
                logit('Factory: disconnected insert watcher');
            }
            // destroy the controller if one exists for the document
            var pc = this.controllers[page_id];
            if(pc) {
                pc.shutdown();
                delete this.controllers[page_id];
                logit('Factory: destroyed outfox controller');
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
            logit('Factory: disconnected insert watcher');
            // create the controller
            this._createController(page_id, outfox_node.ownerDocument);
        }
    },
    
    /**
     * Called when a service fails after its launch by a ServerProxy. Removes
     * all references to the service from this factory.
     *
     * @param json JSON encoded failed service response object
     */
    _onFailedService: function(json) {
        // decode to a response object
        var resp = utils.fromJson(json);
        // get the proxy for the service
        var proxy = this.services[resp.service];
        // do nothing if we don't have a proxy for the service
        if(!proxy) return;
        // shutdown service proxy object
        proxy.shutdown();
        // remove reference to the proxy
        delete this.services[resp.service];
    },

    /**
     * Starts a service if it is not already started. Otherwise, sends the 
     * start request along to the running service so that it can account for 
     * its use by a new page. Should be called by a page before sending any
     * command to the service. Throws an exception on service launch failure.
     *
     * @param page_id ID of the page requesting the service start
     * @param service Name of the service to start
     * @param ob Observer function for service responses
     */
    startService: function(page_id, service, ob) {
        // check if the service is already started
        var proxy = this.services[service];
        if(!proxy) {
            // create a new proxy, letting exceptions during creation bubble
            proxy = new outfox.ServerProxy(service);
            // register our fail service method as an observer for the
            // special all pages * id
            proxy.addObserver('*', utils.bind(this, this._onFailedService));
            // store the proxy for future requests
            this.services[service] = proxy;
        }
        // add the requester as an observer
        proxy.addObserver(page_id, ob);
        logit('Factory: started service');
    },

    /**
     * Stops a service if this is the last page using it. Otherwise, decrements
     * the reference counter on the service. Should be called by a page after
     * it has received the stopped or failed service response.
     *
     * @param page_id ID of the page requesting the service stop
     * @param service Name of the service to stop
     */
    stopService: function(page_id, service) {
        logit('Factory: stopping service', page_id, service);
        // check if the service started
        var proxy = this.services[service];
        // ignore stops if the service is not started or has already failed
        // and was removed
        logit('proxy', proxy);
        if(!proxy) return;
        // remove the requester as an observer
        var count = proxy.removeObserver(page_id);
        logit('count', count);
        if(count <= 1) {
            logit('Factory: shutting down service');
            // shutdown the proxy
            proxy.shutdown();
            // remove reference to the proxy
            delete this.services[service];
        }
    },

    /**
     * Routes a command from a page to a running service.
     * 
     * @param page_id ID of the page requesting the service stop
     * @param service Name of the service to receive the command
     * @param json JSON encoded command
     */
    send: function(page_id, service, json) {
        logit('Factory: send', page_id, service, json);
        // locate the proper proxy
        var proxy = this.services[service];
        // ignore sends if service not started
        if(!proxy) return;
        // invoke the send method of the proxy
        proxy.send(page_id, json);
        logit('Factory: sent');
    }
});

// allow one factory instance per window
var factory = new outfox.Factory();