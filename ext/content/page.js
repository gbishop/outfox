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

/**
 * Manages commands flowing to / from Outfox on a page. Takes special action
 * to start / stop services. Attempts to provide local file names for content
 * cached by Firefox for URLs.
 */
utils.declare('outfox.PageController', null, {
    /**
     * Creates a cache controller. Starts listening to to the outgoing queue
     * of commands on the page.
     *
     * @param id Page id of the page to control
     * @param doc Document object for the page
     * @param factory Factory that created this controller and can create
     *   server proxies as well
     */
    constructor: function(id, doc, factory) {
        this.id = id;
        this.doc = doc;
        this.factory = factory;
        
        // track started services
        this.services = {};

        // create cache session
        this.cache = new outfox.CacheController();

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
            
        // immediately report version number
        var ver = {action: 'initialized-outfox', value: VERSION};
        var json = utils.toJson(ver);
        this._respond(json);

        // run through everything waiting in the outgoing queue and process it 
        while(this.out_queue.firstChild) {
            // handler removes nodes for us
            this._onRequest({'target' : this.out_queue.firstChild});
        }

        logit('PageController: initialized');
    },

    /**
     * Stops listening for responses from all services. Unregisters the 
     * listener for outgoing queue events.
     */
    shutdown: function() {
        // unregister all listeners
        this.tokens.forEach(utils.disconnect);
        // stop all services for this page without waiting for a response
        var services = this.services;
        for(var service in services) {
            this.factory.stopService(this.id, service);
            delete this.services[service];
        }
        logit('Page: shutdown');
    },
    
    /**
     * Inserts a response from a service into the incoming DOM queue.
     *
     * @param json JSON encoding of the response object
     */
    _respond: function(json) {
        // add a node with the incoming json
        var tn = this.doc.createTextNode(json);
        this.in_queue.appendChild(tn);
    },

    /**
     * Called when the the in-page JS inserts a command into the outgoing
     * DOM queue.
     *
     * @param event DOM event
     */
    _onRequest: function(event) {
        var node = event.target;
        // destroy request node immediately to prevent leftovers
        this.out_queue.removeChild(node);
        if(node.nodeName == '#text') {
            // pull out json encoded command
            var json = node.nodeValue;
            logit('PageController: request', json);
            // decode to an object for internal use
            var cmd = utils.fromJson(json);
            if(cmd.action == 'start-service') {
                // start a new service
                var success = this._onStartService(cmd);
                logit('PageController: success launching service', success);
                // don't send the command if the service failed to start
                if(!success) return;
            } else if(cmd.cache) {
                // use content from the browser disk cache if possible
                // or try to cache it if not available
                json = this._onCacheable(cmd);
            }
            // send the command to the service proxy via the factory
            this.factory.send(this.id, cmd.service, json);
        }
    },

    /**
     * Called when a service responds to this page.
     *
     * @param json JSON encoded response object
     */
    _onResponse: function(json) {
        var cmd = utils.fromJson(json);
        if(cmd.action == 'stopped-service' || cmd.action == 'failed-service') {
            // inform the factory that this page is no longer interested in
            // the service that failed or stopped
            this.factory.stopService(this.id, cmd.service)
            delete this.services[cmd.service];
        }
        // put the response in the incoming queue
        this._respond(json);
    },
    
    /**
     * Called to handle a start service command from the page. Instructs the
     * factory to start the service. If starting fails synchronously, return
     * false to avoid sending the command along to the external service.
     *
     * @param cmd Start service command
     * @return True if the factory did not report an error starting the service
     *         False if the factory reported an error
     */
    _onStartService: function(cmd) {
        try {
            // ensure the service exists before sending the command
            this.factory.startService(this.id, cmd.service, 
                utils.bind(this, this._onResponse));
        } catch(e) {
            // put the exception into the incoming queue as a service failure
            var json = this._buildFailure(cmd.service, e.message);
            this._respond(json);
            return false;
        }
        this.services[cmd.service] = true;
        logit('PageController: started service');
        return true;
    },

    /**
     * Called to handle a command that has a URL with potentially cacheable
     * content. Checks if the content of the URL is cached. If not, attempts
     * to cache it and marks the command as deferred. Registers a callback to
     * later send a deferred result to the service.
     *
     * @param cmd Command with a URL
     * @return JSON encoded command updated with URL info or deferred marker
     */
    _onCacheable: function(cmd) {
        // request containing a URL that we might be able to cache
        var fn;
        // check if url is cached
        var obj = this.cache.getLocalFilename(cmd.url);
        if(obj.state == 'ok') {
            // make the command with the local cached copy filename
            // in case the external server can make use of it instead
            cmd.filename = obj.target;
        } else if(obj.state != 'uncacheable') {
            // define a callback for when the prefetch completes and
            // the cache entry is opened for filename access
            var self = this;
            var obs = function(reqid, filename, invalid) {
                // change the action to indicate a deferred result
                // which can be paired with the original based on the
                // deferred request id
                cmd.action = 'deferred-result';
                // indicate that the url couldn't even be fetched so the
                // service doesn't waste time doing it again
                cmd.invalid = invalid;
                if(filename) {
                    // attach the filename, if it exists
                    cmd.filename = filename;
                }
                // send the command to the proper service
                self.factory.send(self.id, cmd.service, utils.toJson(cmd));
            }
            if(obj.state == 'missing') {
                // fetch to cache
                var reqid = this.cache.fetch(cmd.url, obs);
            } else if(obj.state == 'pending') {
                // monitor while pending
                var reqid = this.cache.monitor(cmd.url, obs);
            }
            // mark command as deferred for now
            cmd.deferred = reqid;
        }
        // nothing to do for the uncacheable state
        
        // encode updated command as JSON
        return utils.toJson(cmd);
    },
    
    /**
     * Builds a service failed response object, JSON encodes it, and returns 
     * it.
     *
     * @param description Description of the failure
     * @param service Name of the service
     * @return Failure response object
     */
    _buildFailure: function(service, description) {
        var resp = {};
        resp.action = 'failed-service';
        resp.description = description;
        resp.service = service;
        return utils.toJson(resp);
    }
});
