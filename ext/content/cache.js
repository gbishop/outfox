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
        // @todo: need second session for non-stream based resources
        this.reqid = 0;
        logit('CacheController: initialized');
    },

    /**
     * Gets the local disk cache filename for the given URL.
     *
     * @param url URL key for the cache
     */
    getLocalFilename: function(url) {
        // get canonical url to match with cache
        var uri = this.ios.newURI(url, null, null);
        url = uri.asciiSpec;
        try {
            var entry = this.sess.openCacheEntry(url, this.nsic.ACCESS_READ, this.nsic.BLOCKING);
        } catch(e) {
            return null;
        }
        // this may throw an exception; if it does, it means this item will
        // never be available in the disk cache
        var target = entry.file.path;
        logit('CacheController: found cached file at', target);
        entry.close();
        return target;
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
        logit('CacheController: fetching url for cache', url);

        var reqid = this.reqid++;
        var req = new XMLHttpRequest();
        req.mozBackgroundRequest = true;
        req.open('GET', url, true);
        // define a callback for asynchronous cache entry opening
        // can't do sync within the ready state change context because the
        //  cache entry is still held open by the xhr in there (deadlock!)
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
                logit('CacheController: invoking observer with filename', target);
                // invoke the external observer with the filename
                observer(reqid, target, false);
            }
        };
        
        var self = this;
        req.onreadystatechange = function(event) {
            logit('CacheController: ready state change', req.readyState);
            if(req.readyState == 4) {
                logit('onreadystatechange status', req.status);
                // http gives 200 on success, ftp or file gives 0
                if(req.status == 200 || req.status == 0) {
                    // fetch the info from the cache asynchronously
                    setTimeout(function() {
                        try {
                            self.sess.asyncOpenCacheEntry(url, 
                                self.nsic.ACCESS_READ,
                                cache_obs);
                                logit('CacheController: opened new cache entry');
                            } catch (e) {
                                // still need to callback with null so deferred
                                // requests can be fulfilled
                                logit('CacheController: failed to open new cache entry');
                                observer(reqid, null, false);
                            }
                        }, 0);
                } else {
                    // still need to callback with null as the filename so any
                    // deferred requests can be fulfilled
                    logit('CacheController: failed to fetch new cache entry');
                    observer(reqid, null, true);
                }
            }
        };
        
        req.send(null);
        return reqid;
    }
});