/*
    Copyright (C) 2018, Michi-F

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as
    published by the Free Software Foundation, either version 3 of the
    License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
*/

// usage: var recaptchaV2InteractiveResponseGrabber = new recaptchaV2InteractiveResponseGrabber("captchaIframeId","captchaIframeName",pyloadCaptchaResponseCallbackFunction,pyloadIframeReadyFunction);
// iframeId, iframeName: <iframe id="iframeId" name="iframeName"> of the iframe which shows the page to manually solve the captcha
// pyloadCaptchaResponseCallbackFunction: this callback function is called after the captcha response is grabbed
// this function should take one argument: the captcha response (grecaptcha.getResponse(), string).
// pyloadIframeReadyFunction: this callback function is called after the iframe is loaded and the captcha is ready
function recaptchaV2InteractiveResponseGrabber(iframeId, iframeName, captchaResponseCallbackFunction, iframeReadyFunction)
{
    this._iframeId = iframeId;
    this._iframeName = iframeName;
    this._captchaResponseCallbackFunction = captchaResponseCallbackFunction;
    this._iframeReadyFunction = iframeReadyFunction;
    
    // register event listener for communication with iframe
    $("#"+this._iframeId).on("load", this, this.iframeLoaded);
    $(window).on('message', this, this.windowEventListener);
    
    this._active = false; // true: link grabbing is running, false: standby
    this._sitekey = null;
}

// action codes for communication with iframe via postMessage
recaptchaV2InteractiveResponseGrabber.prototype.actionCodes =
{
    activate:"activateRecaptchaV2Interactive",
    activated:"activatedRecaptchaV2Interactive",
    sendRecaptchaResponse:"sendRecaptchaResponse"
};

// this function listens to messages from the tampermonkey script in the iframe
recaptchaV2InteractiveResponseGrabber.prototype.windowEventListener = function(e)
{
    responseGrabberInstance = e.data;
    var request = JSON.parse(e.originalEvent.data);
    if(request.actionCode == responseGrabberInstance.actionCodes.sendRecaptchaResponse)
    {
        // we got the recaptcha response! pass it to the callback function
        responseGrabberInstance._captchaResponseCallbackFunction(request.value);
        
        // deactivate
        responseGrabberInstance._active = false;
        this._sitekey = null;
    }
    else if(request.actionCode == responseGrabberInstance.actionCodes.activated)
    {
        responseGrabberInstance._iframeReadyFunction();
    }
}
       
recaptchaV2InteractiveResponseGrabber.prototype.grabRecaptchaV2InteractiveResponse = function(downloadLink, sitekey)
{
    // activate
    this._active = true;
    this._sitekey = sitekey;
    $("#"+this._iframeId).attr("src",downloadLink);
}

//this function is called when the iframe is loaded, and it activates the link grabber of the tampermonkey script
recaptchaV2InteractiveResponseGrabber.prototype.iframeLoaded = function(event)
{
    responseGrabberInstance = event.data;
    if(responseGrabberInstance._active)
    {
        returnObject = {actionCode: responseGrabberInstance.actionCodes.activate, value:responseGrabberInstance._sitekey};
        $("#"+responseGrabberInstance._iframeId).get(0).contentWindow.postMessage(JSON.stringify(returnObject),"*");
    }
}

recaptchaV2InteractiveResponseGrabber.prototype.clearEventlisteners = function()
{
    // clean up event listeners
    $("#"+this._iframeId).off("load", this, this.iframeLoaded);
    $(window).off('message', this, this.windowEventListener);
}
