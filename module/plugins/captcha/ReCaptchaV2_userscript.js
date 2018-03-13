// ==UserScript==
// @name         Pyload Script for interactive reCAPTCHA V2
// @namespace    https://pyload.net/
// @version      0.13
// @author       Michi-F
// @description  Pyload Script for interactive reCAPTCHA V2
// @homepage     https://github.com/pyload/pyload
// @icon         https://raw.githubusercontent.com/pyload/pyload/stable/module/web/media/img/favicon.ico
// @updateURL    https://raw.githubusercontent.com/pyload/pyload/stable/module/plugins/captcha/ReCaptchaV2_userscript.js
// @downloadURL  https://raw.githubusercontent.com/pyload/pyload/stable/module/plugins/captcha/ReCaptchaV2_userscript.js
// @supportURL   https://github.com/pyload/pyload/issues
// @grant        none
//
// @match        *://*.share-online.biz/*
// @match        *://*.uploaded.net/*
// @match        *://filer.net/*
//
// ==/UserScript==

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

(function() {
    'use strict';

    // action codes for communication with pyload main page
    window.pyloadActionCodes = {
        activate:"activateRecaptchaV2Interactive",
        activated:"activatedRecaptchaV2Interactive",
        sendRecaptchaResponse:"sendRecaptchaResponse"
    };

    // this function listens to messages from the pyload main page
    window.addEventListener('message', function(e) {
        var request = JSON.parse(e.data);
        var returnObject = null;
        if(request.actionCode == window.pyloadActionCodes.activate)
        {
            window.pyloadRecaptchaV2InteractiveSitekey = request.value;

            while(document.children[0].childElementCount > 0)
            {
                document.children[0].removeChild(document.children[0].children[0]);
            }
            document.children[0].innerHTML = '<html><style>div{background-color:transparent!important;}</style><head></head><body><div id="captchadiv"></div></body></html>';

            // function that is called when the captcha is completed
            window.pyloadCaptchaCompletedCallback = function()
            {
                if(pyloadIsCaptchaCompleted())
                {
                    // get captcha response
                    var recaptchaResponse = grecaptcha.getResponse();
                    // yes, we got a valid response!
                    // now pass the download link to the callback function on the pyload page
                    var returnObject = {actionCode: window.pyloadActionCodes.sendRecaptchaResponse, value: recaptchaResponse};
                    parent.postMessage(JSON.stringify(returnObject),"*");
                }
            };

            // checks if the captcha is completed
            window.pyloadIsCaptchaCompleted = function()
            {
                return grecaptcha && grecaptcha.getResponse().length !== 0;
            };

            window.captchaOnloadCallback = function()
            {
                grecaptcha.render(
                    document.getElementById("captchadiv"),
                    {sitekey:window.pyloadRecaptchaV2InteractiveSitekey, callback: pyloadCaptchaCompletedCallback}
                );

                var returnObject = {actionCode: window.pyloadActionCodes.activated, value: true};
                parent.postMessage(JSON.stringify(returnObject),"*");
            };

            var js_script = document.createElement('script');
            js_script.type = "text/javascript";
            js_script.src = "https://www.google.com/recaptcha/api.js?onload=captchaOnloadCallback&render=explicit";
            js_script.async = true;
            document.getElementsByTagName('head')[0].appendChild(js_script);
        }
    });
})();