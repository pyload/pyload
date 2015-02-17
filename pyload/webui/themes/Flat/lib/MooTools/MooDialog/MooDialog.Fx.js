/*
---
name: MooDialog.Fx
description: Overwrite the default events so the Dialogs are using Fx on open and close
authors: Arian Stolwijk
license: MIT-style license
requires: [Core/Fx.Tween, Overlay]
provides: MooDialog.Fx
...
*/


MooDialog.implement('options', {

	duration: 400,
	closeOnOverlayClick: true,

	onInitialize: function(wrapper){
		this.fx = new Fx.Tween(wrapper, {
			property: 'opacity',
			duration: this.options.duration
		}).set(0);
		this.overlay = new Overlay(this.options.inject, {
			duration: this.options.duration
		});
		if (this.options.closeOnOverlayClick) this.overlay.addEvent('click', this.close.bind(this));

		this.addEvent('hide', function(){
			if (this.options.destroyOnHide) this.overlay.overlay.destroy();
		}.bind(this));
	},

	onBeforeOpen: function(wrapper){
		this.overlay.open();
		this.fx.start(1).chain(function(){
			this.fireEvent('show');
		}.bind(this));
	},

	onBeforeClose: function(wrapper){
		this.overlay.close();
		this.fx.start(0).chain(function(){
			this.fireEvent('hide');
		}.bind(this));
	}

});
