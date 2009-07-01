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
 * Manages which sites the user has approved to access Outfox services on a
 * permanent basis.
 */
utils.declare('outfox.AccessController', null, {
    constructor: function() {
        // database file located in profile root
        var file = Components.classes["@mozilla.org/file/directory_service;1"]  
                   .getService(Components.interfaces.nsIProperties)  
                   .get("ProfD", Components.interfaces.nsIFile);  
        file.append("outfox.sqlite");  
        // storage service
        var storageService = Components.classes["@mozilla.org/storage/service;1"]  
                             .getService(Components.interfaces.mozIStorageService);  
        this.conn = storageService.openDatabase(file);
        // create access table if it doesn't exist
        if(!this.conn.tableExists('access')) {
            this.conn.createTable('access', 'uriKey TEXT UNIQUE, allowed INTEGER');
            //this.conn.executeSimpleSQL('CREATE INDEX uriKeyIndex ON access(uriKey)');
        }
    },
    
    /**
     * Initialize the instance.
     */
    initialize: function() {
        // currently a no-op
    },
    
    /**
     * Closes the database connection.
     */
    shutdown: function() {
        this.conn.close();
    },
    
    /**
     * Gets a key for the access table from a URI of a document.
     */
    getKeyFromURI: function(uri) {
        if(uri.port < 0) {
            return uri.scheme+'://'+uri.host;
        } else {
            return uri.scheme+'://'+uri.host+':'+uri.port;
        }
    },
    
    /**
     * Gets if a URI has access to outfox services or not.
     *
     * @param key Access table key
     * @return True, false, or null meaning permission is not in the db
     */
    canURIAccess: function(key) {
        var statement = this.conn.createStatement('SELECT * FROM access WHERE uriKey = :uriKeyValue');
        statement.bindUTF8StringParameter(0, key);
        if(statement.executeStep()) {
            var val = statement.getInt32(1);
            return val;
        }
        logit('done execute step');
        return null;
    },
    
    /**
     * Give the site permanent access to outfox until the user revokes it.
     *
     * @param key Access table key
     */
    allowURIAccess: function(key) {
        var statement = this.conn.createStatement('INSERT OR REPLACE INTO access (uriKey,allowed) values (:uriKeyValue, 1)');
        statement.bindUTF8StringParameter(0, key);
        statement.execute();
    },

    /**
     * Prevent site access outfox permanently until the user restores it.
     *
     * @param key Access table key
     */    
    denyURIAccess: function(key) {
        var statement = this.conn.createStatement('INSERT OR REPLACE INTO access (uriKey,allowed) values (:uriKeyValue, 0)');
        statement.bindUTF8StringParameter(0, key);
        statement.execute();
    },
   
    /**
     * Remove a permanent decision to allow or deny outfox access for a site.
     *
     * @param key Access table key
     */
    clearURIAccess: function(key) {
        var statement = this.conn.createStatement('DELETE FROM access WHERE uriKey = :uriKeyValue');
        statement.bindUTF8StringParameter(0, key);
        statement.execute();
    }
});