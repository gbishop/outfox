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
* 
*/

// constants for cache exceptions
NS_ERROR_CACHE_WAIT_FOR_VALIDATION = 2152398912;

/**
 * Manages the caching of URL data in the Firefox disk cache for services.
 */
utils.declare('outfox.CacheController', null, {
    /**
     * Creates component instances for the cache service, network IO service,
     * and HTTP session.
     */
    constructor: function() {
        var cs = Components.classes["@mozilla.org/network/cache-service;1"].getService(Components.interfaces.nsICacheService);
        this.ios = Components.classes["@mozilla.org/network/io-service;1"].getService(Components.interfaces.nsIIOService);
        this.nsic = Components.interfaces.nsICache;
        this.sess = cs.createSession('HTTP', this.nsic.STORE_ON_DISK, this.nsic.STREAM_BASED);
        this.reqid = 0;
        this.pending = [];
        logit('CacheController: initialized');
    },

    /**
     * Gets the local disk cache filename for the given URL.
     *
     * @param url URL key for the cache
     * @return Object with state and target (optional) properties
     */
    getLocalFilename: function(url) {
        // get canonical url to match with cache
        var uri = this.ios.newURI(url, null, null);
        url = uri.asciiSpec;
        try {
            var entry = this.sess.openCacheEntry(url, this.nsic.ACCESS_READ, 
                this.nsic.NON_BLOCKING);
        } catch(e) {
            if(e.result == NS_ERROR_CACHE_WAIT_FOR_VALIDATION) {
                // file is downloading
                logit('CacheController: cache wait for validation', url);
                return {state : 'pending'};
            } else {
                logit('CacheController: cache entry missing', url);
                // file is not in the cache, but could be added
                return {state : 'missing'};
            }
        }
        try {
            var target = entry.file.path;
        } catch(e) {
            logit('CacheController: not disk cacheable', url);
            // file is uncacheable on disk
            return {state : 'uncacheable'};
        }
        entry.close();
        logit('CacheController: cache file', target);
        return {state : 'ok', target : target};
    },
    
    /**
     * Monitors a URL for cache entry validation after a fetch.
     *
     * @param url String URL
     * @param observer Observer to invoke when the cache item is free
     */
    monitor: function(url, observer) {
        // get canonical url
        var uri = this.ios.newURI(url, null, null);
        url = uri.asciiSpec;
        // generate new request ID
        var reqid = this.reqid++;
        // store the url and observer for later notification
        this.pending.push({url : url, reqid : reqid, observer : observer});
        return reqid;
    },
    
    /**
     * Processes pending URLs monitored for cache validation.
     *
     * @param url String URL
     * @param filename String filename of the cached entry or null
     * @param invalid True of invalid URL, false if valid
     */
    _processPending: function(url, filename, invalid) {
        var saved = [];
        for(var i=0; i < this.pending.length; i++) {
            if(this.pending[i].url == url) {
                // invoke the observer
                this.pending[i].observer(this.pending[i].reqid, filename, 
                    invalid);
            } else {
                // still pending, save for later
                saved.push(this.pending[i]);
            }
        }
        this.pending = saved;
    },

    /** 
     * Fetches the data at the given URL and places it in the cache if
     * possible. Notifies the observer when the data is available.
     *
     * @param url String URL 
     * @param observer Observer to invoke when the data is available locally
     */
    fetch: function(url, observer) {
        // get canonical url
        var uri = this.ios.newURI(url, null, null);
        url = uri.asciiSpec;

        var reqid = this.reqid++;
        var req = new XMLHttpRequest();
        req.mozBackgroundRequest = true;
        req.open('GET', url, true);
        // define a callback for asynchronous cache entry opening
        // can't do sync within the ready state change context because the
        //  cache entry is still held open by the xhr in there (deadlock!)
        var self = this;
        var cache_obs = {
            onCacheEntryAvailable: function(entry, access, status) {
                try {
                    var target = entry.file.path;
                } catch(e) {
                    // not cacheable, so make filename null
                    var target = null;
                }
                // close entry before proceeding
                entry.close();
                logit('CacheController: opened new cache entry', target);
                // invoke the external observer with the filename
                observer(reqid, target, false);
                // pump pending requests
                self._processPending(url, target, false);
            }
        };
        req.onreadystatechange = function(event) {
            if(req.readyState == 4) {
                // http gives 200 on success, ftp or file gives 0
                if(req.status == 200 || req.status == 0) {
                    // fetch the info from the cache asynchronously
                    setTimeout(function() {
                        try {
                            self.sess.asyncOpenCacheEntry(url, 
                                self.nsic.ACCESS_READ,
                                cache_obs);
                            } catch (e) {
                                // still need to callback with null so deferred
                                // requests can be fulfilled
                                logit('CacheController: failed to open new cache entry');
                                observer(reqid, null, false);
                                // pump pending requests
                                self._processPending(url, null, false);
                            }
                        }, 0);
                } else {
                    // still need to callback with null as the filename so any
                    // deferred requests can be fulfilled
                    logit('CacheController: failed to fetch new cache entry');
                    observer(reqid, null, true);
                    // pump pending requests
                    self._processPending(url, null, true);
                }
            }
        };
        
        req.send(null);
        return reqid;
    }
});