/**
 * @license
 * jquery.peekABar 1.0.1 <http://kunalnagar.github.io/jquery.peekABar>
 * Copyright 2015 Kunal Nagar
 * Available under MIT license
 */
;(function($) {

	/** Enable strict mode. */
	'use strict';

	$.peekABar = function(options) {

		var that = this,
			rand = parseInt(Math.random() * 100000000, 0);

		/** Instance */
		this.bar = {};

		/** Settings */
		this.settings = {};

		/** Defaults */
		var defaults = {
			html: 'Your Message Here',
			delay: 3000,
			autohide: false,
			padding: '1em',
			backgroundColor: 'rgb(195, 195, 195)',
			animation: {
				type: 'slide',
				duration: 'slow'
			},
			cssClass: null,
			opacity: '1',
			position: 'top',

			onShow: function() {},
			onHide: function() {},

			closeOnClick: false
		};

		/** Initialise the plugin */
		var init = function() {
			that.settings = $.extend({}, defaults, options);
			_create();
			_applyCustomSettings();
		};

		/** Show the Bar */
		this.show = function(args) {
			if(args !== undefined) {
				if(args.html) {
					this.bar.html(args.html);
				}
			}
			switch (this.settings.animation.type) {
				case 'slide':
					this.bar.slideDown(that.settings.animation.duration);
					break;
				case 'fade':
					this.bar.fadeIn(that.settings.animation.duration);
					break;
			}
			if(this.settings.autohide) {
				setTimeout(function () {
					that.hide();
				}, this.settings.delay);
			}
			this.settings.onShow.call(this, args);
		};

		/** Hide the Bar */
		this.hide = function() {
			switch (this.settings.animation.type) {
				case 'slide':
					this.bar.slideUp(that.settings.animation.duration);
					break;
				case 'fade':
					this.bar.fadeOut(that.settings.animation.duration);
					break;
			}
			this.settings.onHide.call(this);
		};

		/** Create the Bar */
		var _create = function() {
			that.bar = $('<div></div>').addClass('peek-a-bar').attr('id', '__peek_a_bar_' + rand);
			$('html').append(that.bar);
			that.bar.hide();
		};

		/** Apply Custom Bar Settings */
		var _applyCustomSettings = function() {
			_applyHTML();
			_applyAutohide();
			_applyPadding();
			_applyBackgroundColor();
			_applyOpacity();
			_applyCSSClass();
			_applyPosition();
			_applyCloseOnClick();
		};

		/** Set Custom Bar HTML */
		var _applyHTML = function() {
			that.bar.html(that.settings.html);
		};

		/** Autohide the Bar */
		var _applyAutohide = function() {
			if(that.settings.autohide) {
				setTimeout(function () {
					that.hide();
				}, that.settings.delay);
			}
		};

		/** Apply Padding */
		var _applyPadding = function() {
			that.bar.css('padding', that.settings.padding);
		};

		/** Apply Background Color */
		var _applyBackgroundColor = function() {
			that.bar.css('background-color', that.settings.backgroundColor);
		};

		/** Apply Custom CSS Class */
		var _applyCSSClass = function() {
			if(that.settings.cssClass !== null) {
				that.bar.addClass(that.settings.cssClass);
			}
		};

		/** Apply Opacity */
		var _applyOpacity = function() {
			that.bar.css('opacity', that.settings.opacity);
		};

		/** Apply Position where the Bar should be shown */
		var _applyPosition = function() {
			switch(that.settings.position) {
				case 'top':
					that.bar.css('top', 0);
					break;
				case 'bottom':
					that.bar.css('bottom', 0);
					break;
				default:
					that.bar.css('top', 0);
			}
		};

		/** Close the bar on click */
		var _applyCloseOnClick = function() {
			if(that.settings.closeOnClick) {
				that.bar.click(function() {
					that.hide();
				});
			}
		};

		init();

		return this;
	}

})(jQuery);
