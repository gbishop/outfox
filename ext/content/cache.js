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
utils.declare('outfox.CacheController', null, {
    constructor: function() {
	var cs = Components.classes["@mozilla.org/network/cache-service;1"].getService(Components.interfaces.nsICacheService);
	this.fs = Components.classes["@mozilla.org/prefetch-service;1"].getService(Components.interfaces.nsIPrefetchService);
	this.ios = Components.classes["@mozilla.org/network/io-service;1"].getService(Components.interfaces.nsIIOService);
	this.nsic = Components.interfaces.nsICache;
	this.sess = cs.createSession('HTTP', this.nsic.STORE_ANYWHERE,
				     this.nsic.STREAM_BASED);
    },

    getLocalFilename: function(url) {
	try {
	    var entry = this.sess.openCacheEntry(url, 
		this.nsic.ACCESS_READ, this.nsic.BLOCKING);
	} catch(e) {
	    return null;
	}
	var target = entry.file.target;
	entry.close();
	return target;
    },

    fetch: function(url, observer) {
	var req = new XMLHttpRequest();
	req.mozBackgroundRequest = true;
	req.open('GET', url, true);
	req.onreadystatechange = function(event) {
	    if(req.readyState == 4) {
		// http, ftp, or file
		if(req.status == 200 || req.status == 0) {
		    observer(req, event);
		} else {
		    logit('XHR error');
		}
	    }
	};
	req.send(null); 
    }
});
