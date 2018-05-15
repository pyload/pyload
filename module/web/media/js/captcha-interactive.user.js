// ==UserScript==
// @name         pyLoad Script for Interactive Captcha
// @namespace    https://pyload.net/
// @version      0.14
// @author       Michi-F
// @description  pyLoad Script for Interactive Captcha
// @homepage     https://github.com/pyload/pyload
// @icon         https://raw.githubusercontent.com/pyload/pyload/stable/module/web/media/img/favicon.ico
// @updateURL    https://raw.githubusercontent.com/pyload/pyload/stable/module/web/media/js/captcha-interactive.user.js
// @downloadURL  https://raw.githubusercontent.com/pyload/pyload/stable/module/web/media/js/captcha-interactive.user.js
// @supportURL   https://github.com/pyload/pyload/issues
// @grant        none
// @run-at       document-start
// @require      https://kjur.github.io/jsrsasign/jsrsasign-all-min.js
//
// @match        *://*/*
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

    window.gpyload = {
        actionCodes : { // action codes for communication with pyload main page
            activate: "pyloadActivateInteractive",
            activated: "pyloadActivatedInteractive",
            getSize: "pyloadIframeGetSize",
            size: "pyloadIframeSize",
            submitResponse: "pyloadSubmitResponse"
        },
        getElementSize : function(element) {
            if (!element.getBoundingClientRect) {
                return {
                    width: element.offsetWidth,
                    height: element.offsetHeight
                }
            }
            var rect = element.getBoundingClientRect();
            return {
                width: Math.round(rect.width),
                height: Math.round(rect.height)
            }
        },
        data : {}
    };

    // this function listens to messages from the pyload main page
    window.addEventListener('message', function(e) {
        var request = JSON.parse(e.data);

        if(request.actionCode === gpyload.actionCodes.activate) {
            if (request.params.script) {
                var sig = new KJUR.crypto.Signature({"alg": "SHA384withRSA", "prov": 'cryptojs/jsrsa'});
                sig.init("-----BEGIN PUBLIC KEY-----\n" +
                    "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAuEHE4uAeTeEQjIwB//YH\n" +
                    "Gl5e058aJRCRyOvApv1iC1ZQgXGHopgEd528+AtkAZKdCRkoNCWda7L/hROpZNjq\n" +
                    "xgO5NjjlBnotntQiZ6xr7A4Kfdctmw1DPcv/dkp6SXRpAAw8BE9CctZ3H7cE/4UT\n" +
                    "FIJOYQQXF2dcBTWLnUAjesNoHBz0uHTdvBIwJdfdUIrNMI4IYXL4mq9bpKNvrwrb\n" +
                    "iNhSqN0yV8sanofZmDX4JUmVGpWIkpX0u+LA4bJlaylwPxjuWyIn5OBED0cdqpbO\n" +
                    "7t7Qtl5Yu639DF1eZDR054d9OB3iKZX1a6DTg4C5DWMIcU9TsLDm/JJKGLWRxcJJ\n" +
                    "fwIDAQAB\n" +
                    "-----END PUBLIC KEY----- ");
                sig.updateString(request.params.script.code);
                if (sig.verify(request.params.script.signature)) {
                    eval(request.params.script.code);
                } else {
                    console.log("pyLoad: Script signature verification failed")
                }
            }
        }
    });
})();