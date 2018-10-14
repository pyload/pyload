/*
---
name: MooDialog.Confirm
description: Creates an Confirm Dialog
authors: Arian Stolwijk
license:  MIT-style license
requires: MooDialog
provides: [MooDialog.Confirm, Element.confirmLinkClick, Element.confirmFormSubmit]
...
*/


MooDialog.Confirm = new Class({

	Extends: MooDialog,

	options: {
		okText: 'Ok',
		cancelText: 'Cancel',
		focus: true,
		textPClass: 'MooDialogConfirm'
	},

	initialize: function(msg, fn, fn1, options){
		this.parent(options);
		var emptyFn = function(){},
			self = this;

		var buttons = [
			{fn: fn || emptyFn, txt: this.options.okText},
			{fn: fn1 || emptyFn, txt: this.options.cancelText}
		].map(function(button){
			return new Element('button', {
				events: {
					click: function(){
						button.fn();
						self.close();
					}
				},
				text: button.txt
			});
		});

		this.setContent(
			new Element('p.' + this.options.textPClass, {text: msg}),
			new Element('div.buttons').adopt(buttons)
		);
		if (this.options.autoOpen) this.open();

		if(this.options.focus) this.addEvent('show', function(){
			buttons[1].focus();
		});

	}
});


Element.implement({

	confirmLinkClick: function(msg, options){
		this.addEvent('click', function(e){
			e.stop();
			new MooDialog.Confirm(msg, function(){
				location.href = this.get('href');
			}.bind(this), null, options)
		});
		return this;
	},

	confirmFormSubmit: function(msg, options){
		this.addEvent('submit', function(e){
			e.stop();
			new MooDialog.Confirm(msg, function(){
				this.submit();
			}.bind(this), null, options)
		}.bind(this));
		return this;
	}

});
