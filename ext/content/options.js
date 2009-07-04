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
 */

/**
 * Manages the Outfox options dialog with the list of sites a user has 
 * permanently allowed or denied access to services.
 */
utils.declare('outfox.OptionsController', null, {
    constructor: function() {
        // per origin (scheme, host, port) white/black list for outfox access
        this.access = new outfox.AccessController();
    },
    
    /**
     * Initializes the permissions box in the dialog with list items that allow
     * allow and deny control for each site.
     */
    initialize: function() {
        // get ref to permissions list in dialog
        this.perms_list = document.getElementById('outfoxPermsList');
        // get all sites and permissions
        this.access.initialize();
        var rows = this.access.getAllPermissions();

        // get blueprint for permission row
        var bp = document.getElementById('outfoxBlueprints')
                 .getElementsByAttribute('role','permission')[0];
        // build rows in access list
        for(var i=0; i<rows.length; i++) {
            var row = rows[i];
            // build new row from blueprint
            var item = bp.cloneNode(true);
            var site = item.getElementsByAttribute('role', 'site')[0];
            site.setAttribute('value', row.key);
            site.setAttribute('control', row.key);
            var allowed = item.getElementsByAttribute('role', 'allowed')[0];
            allowed.setAttribute('value', row.allowed);
            this.perms_list.appendChild(item);
        }
    },

    /**
     * Shuts down the access controller.
     */
    shutdown: function() {
        this.access.shutdown();
    },
    
    /**
     * Gets the site key associated with the given permission list item.
     *
     * @param item richlistitem element
     */
    getKeyForItem: function(item) {
        return item.getElementsByAttribute('role','site')[0]
               .getAttribute('value');
    },
    
    /**
     * Removes the currently selected item from the list and its corresponding
     * site from the permanent access control list.
     */
    onRemoveRow: function() { 
        // get the db key for this item
        var key = this.getKeyForItem(this.perms_list.selectedItem);
        // remote the item from the db
        this.access.clearURIAccess(key);
        // get the selected index
        var i = this.perms_list.selectedIndex;
        // remove the item from the list        
        this.perms_list.removeItemAt(i);
    },
    
    /**
     * Switches a site from allowed to disallowed.
     *
     * @param radio radiogroup element
     */
    onChangeAccess: function(radio) {
        // get if set to allowed or denied
        var allowed = Number(radio.value);
        // get the db key for this item
        var key = this.getKeyForItem(radio.parentNode);
        // update the db
        if(allowed) {
            this.access.allowURIAccess(key);
        } else {
            this.access.denyURIAccess(key);
        }
    }
});

// create an options controller instance
options = new outfox.OptionsController();