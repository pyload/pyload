/*
---
script: purr.js

description: Class to create growl-style popup notifications.

license: MIT-style

authors: [atom smith]

requires:
- core/1.3: [Core, Browser, Array, Function, Number, String, Hash, Event, Class.Extras, Element.Event, Element.Style, Element.Dimensions, Fx.CSS, FX.Tween, Fx.Morph]

provides: [Purr, Element.alert]
...
*/


var Purr = new Class({

	'options': {
		'mode': 'top',
		'position': 'left',
		'elementAlertClass': 'purr-element-alert',
		'elements': {
			'wrapper': 'div',
			'alert': 'div',
			'buttonWrapper': 'div',
			'button': 'button'
		},
		'elementOptions': {
			'wrapper': {
				'styles': {
					'position': 'fixed',
					'z-index': '9999'
				},
				'class': 'purr-wrapper'
			},
			'alert': {
				'class': 'purr-alert',
				'styles': {
					'opacity': '.85'
				}
			},
			'buttonWrapper': {
				'class': 'purr-button-wrapper'
			},
			'button': {
				'class': 'purr-button'
			}
		},
		'alert': {
			'buttons': [],
			'clickDismiss': true,
			'hoverWait': true,
			'hideAfter': 5000,
			'fx': {
				'duration': 500
			},
			'highlight': false,
			'highlightRepeat': false,
			'highlight': {
				'start': '#FF0',
				'end': false
			}
		}
	},

	'Implements': [Options, Events, Chain],

	'initialize': function(options){
		this.setOptions(options);
		this.createWrapper();
		return this;
	},

	'bindAlert': function(){
		return this.alert.bind(this);
	},

	'createWrapper': function(){
		this.wrapper = new Element(this.options.elements.wrapper, this.options.elementOptions.wrapper);
		if(this.options.mode == 'top')
		{
			this.wrapper.setStyle('top', 0);
		}
		else
		{
			this.wrapper.setStyle('bottom', 0);
		}
		document.id(document.body).grab(this.wrapper);
		this.positionWrapper(this.options.position);
	},

	'positionWrapper': function(position){
		if(typeOf(position) == 'object')
		{

			var wrapperCoords = this.getWrapperCoords();

			this.wrapper.setStyles({
				'bottom': '',
				'left': position.x,
				'top': position.y - wrapperCoords.height,
				'position': 'absolute'
			});
		}
		else if(position == 'left')
		{
			this.wrapper.setStyle('left', 0);
		}
		else if(position == 'right')
		{
			this.wrapper.setStyle('right', 0);
		}
		else
		{
			this.wrapper.setStyle('left', (window.innerWidth / 2) - (this.getWrapperCoords().width / 2));
		}
		return this;
	},

	'getWrapperCoords': function(){
		this.wrapper.setStyle('visibility', 'hidden');
		var measurer = this.alert('need something in here to measure');
		var coords = this.wrapper.getCoordinates();
		measurer.destroy();
		this.wrapper.setStyle('visibility','');
		return coords;
	},

	'alert': function(msg, options){

		options = Object.merge({}, this.options.alert, options || {});

		var alert = new Element(this.options.elements.alert, this.options.elementOptions.alert);

		if(typeOf(msg) == 'string')
		{
			alert.set('html', msg);
		}
		else if(typeOf(msg) == 'element')
		{
			alert.grab(msg);
		}
		else if(typeOf(msg) == 'array')
		{
			var alerts = [];
			msg.each(function(m){
				alerts.push(this.alert(m, options));
			}, this);
			return alerts;
		}

		alert.store('options', options);

		if(options.buttons.length > 0)
		{
			options.clickDismiss = false;
			options.hideAfter = false;
			options.hoverWait = false;
			var buttonWrapper = new Element(this.options.elements.buttonWrapper, this.options.elementOptions.buttonWrapper);
			alert.grab(buttonWrapper);
			options.buttons.each(function(button){
				if(button.text != undefined)
				{
					var callbackButton = new Element(this.options.elements.button, this.options.elementOptions.button);
					callbackButton.set('html', button.text);
					if(button.callback != undefined)
					{
						callbackButton.addEvent('click', button.callback.pass(alert));
					}
					if(button.dismiss != undefined && button.dismiss)
					{
						callbackButton.addEvent('click', this.dismiss.pass(alert, this));
					}
					buttonWrapper.grab(callbackButton);
				}
			}, this);
		}
		if(options.className != undefined)
		{
			alert.addClass(options.className);
		}

		this.wrapper.grab(alert, (this.options.mode == 'top') ? 'bottom' : 'top');

		var fx = Object.merge(this.options.alert.fx, options.fx);
		var alertFx = new Fx.Morph(alert, fx);
		alert.store('fx', alertFx);
		this.fadeIn(alert);

		if(options.highlight)
		{
			alertFx.addEvent('complete', function(){
				alert.highlight(options.highlight.start, options.highlight.end);
				if(options.highlightRepeat)
				{
					alert.highlight.periodical(options.highlightRepeat, alert, [options.highlight.start, options.highlight.end]);
				}
			});
		}
		if(options.hideAfter)
		{
			this.dismiss(alert);
		}

		if(options.clickDismiss)
		{
			alert.addEvent('click', function(){
				this.holdUp = false;
				this.dismiss(alert, true);
			}.bind(this));
		}

		if(options.hoverWait)
		{
			alert.addEvents({
				'mouseenter': function(){
					this.holdUp = true;
				}.bind(this),
				'mouseleave': function(){
					this.holdUp = false;
				}.bind(this)
			});
		}

		return alert;
	},

	'fadeIn': function(alert){
		var alertFx = alert.retrieve('fx');
		alertFx.set({
			'opacity': 0
		});
		alertFx.start({
			'opacity': [this.options.elementOptions.alert.styles.opacity, .9].pick(),
		});
	},

	'dismiss': function(alert, now){
		now = now || false;
		var options = alert.retrieve('options');
		if(now)
		{
			this.fadeOut(alert);
		}
		else
		{
			this.fadeOut.delay(options.hideAfter, this, alert);
		}
	},

	'fadeOut': function(alert){
		if(this.holdUp)
		{
			this.dismiss.delay(100, this, [alert, true])
			return null;
		}
		var alertFx = alert.retrieve('fx');
		if(!alertFx)
		{
			return null;
		}
		var to = {
			'opacity': 0
		}
		if(this.options.mode == 'top')
		{
			to['margin-top'] = '-'+alert.offsetHeight+'px';
		}
		else
		{
			to['margin-bottom'] = '-'+alert.offsetHeight+'px';
		}
		alertFx.start(to);
		alertFx.addEvent('complete', function(){
			alert.destroy();
		});
	}
});

Element.implement({

	'alert': function(msg, options){
		var alert = this.retrieve('alert');
		if(!alert)
		{
			options = options || {
				'mode':'top'
			};
			alert = new Purr(options)
			this.store('alert', alert);
		}

		var coords = this.getCoordinates();

		alert.alert(msg, options);

		alert.wrapper.setStyles({
			'bottom': '',
			'left': (coords.left - (alert.wrapper.getWidth() / 2)) + (this.getWidth() / 2),
			'top': coords.top - (alert.wrapper.getHeight()),
			'position': 'absolute'
		});

	}

});