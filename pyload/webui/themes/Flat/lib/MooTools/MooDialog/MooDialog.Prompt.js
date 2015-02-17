/*
---
name: MooDialog.Prompt
description: Creates a Prompt dialog
authors: Arian Stolwijk
license:  MIT-style license
requires: MooDialog
provides: MooDialog.Prompt
...
*/


MooDialog.Prompt = new Class({

	Extends: MooDialog,

	options: {
		okText: 'Ok',
		focus: true,
		textPClass: 'MooDialogPrompt',
		defaultValue: ''
	},

	initialize: function(msg, fn, options){
		this.parent(options);
		if (!fn) fn = function(){};

		var textInput = new Element('input.textInput', {type: 'text', value: this.options.defaultValue}),
			submitButton = new Element('input[type=submit]', {value: this.options.okText}),
			formEvents = {
				submit: function(e){
					e.stop();
					fn(textInput.get('value'));
					this.close();
				}.bind(this)
			};

		this.setContent(
			new Element('p.' + this.options.textPClass, {text: msg}),
			new Element('form.buttons', {events: formEvents}).adopt(textInput, submitButton)
		);
		if (this.options.autoOpen) this.open();

		if (this.options.focus) this.addEvent('show', function(){
			textInput.focus();
		});
	}
});
