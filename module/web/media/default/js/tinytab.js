/*
---
description: TinyTab - Tiny and simple tab handler for Mootools.

license: MIT-style

authors:
- Danillo César de O. Melo

requires:
- core/1.2.4: '*'

provides: TinyTab

...
*/
(function($) {
	this.TinyTab = new Class({
		Implements: Events,
		initialize: function(tabs, contents, opt) {
			this.tabs = tabs;
			this.contents = contents;
            this.header = $("tabsback");
            this.headers = [];
            for(var i =0; i < this.tabs.length; i++){
                this.headers.push("");
            }
			if(!opt) opt = {};
			this.css = opt.selectedClass || 'selected'; 
			this.select(this.tabs[0]);
			tabs.each(function(el){
				el.addEvent('click',function(e){
					this.select(el);
					e.stop();
				}.bind(this));
			}.bind(this));
		},

		select: function(el) {
			this.tabs.removeClass(this.css);
			el.addClass(this.css);
			this.contents.setStyle('display','none');
            var index = this.tabs.indexOf(el);
            this.header.set("text", this.headers[index]);
			var content = this.contents[index];
			content.setStyle('display','block');
			this.fireEvent('change',[content,el]);
		}
	});
})(document.id);