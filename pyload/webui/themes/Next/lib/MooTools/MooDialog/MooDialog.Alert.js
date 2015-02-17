/*
---
name: MooDialog.Alert
description: Creates an Alert dialog
authors: Arian Stolwijk
license:  MIT-style license
requires: MooDialog
provides: MooDialog.Alert
...
*/


MooDialog.Alert = new Class({

	Extends: MooDialog,

	options: {
		okText: 'Ok',
		focus: true,
		textPClass: 'MooDialogAlert'
	},

	initialize: function(msg, options){
		this.parent(options);

		var okButton = new Element('button', {
			events: {
				click: this.close.bind(this)
			},
			text: this.options.okText
		});

		this.setContent(
			new Element('p.' + this.options.textPClass, {text: msg}),
			new Element('div.buttons').adopt(okButton)
		);
		if (this.options.autoOpen) this.open();

		if (this.options.focus) this.addEvent('show', function(){
			okButton.focus()
		});

	}
});

