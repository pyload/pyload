// ==UserScript==
// @name         pyLoad Script for Interactive Captcha
// @namespace    https://pyload.net/
// @version      0.19
// @author       Michi-F, GammaC0de
// @description  pyLoad Script for Interactive Captcha
// @homepage     https://github.com/pyload/pyload
// @icon         https://raw.githubusercontent.com/pyload/pyload/main/src/pyload/webui/app/static/img/favicon.ico
// @updateURL    https://raw.githubusercontent.com/pyload/pyload/main/src/pyload/webui/app/static/js/captcha-interactive.user.js
// @downloadURL  https://raw.githubusercontent.com/pyload/pyload/main/src/pyload/webui/app/static/js/captcha-interactive.user.js
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

    // this function listens to messages from the pyload main page
    window.addEventListener('message', function(e) {
        try {
            var request = JSON.parse(e.data);
        } catch(e) {
            return
        }
        if(request.constructor === {}.constructor && request.actionCode === "pyloadActivateInteractive") {
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
                    window.gpyload = {
                        isVisible : function(element) {
                            var style = window.getComputedStyle(element);
                            return !(style.width === 0 ||
                                    style.height === 0 ||
                                    style.opacity === 0 ||
                                    style.display ==='none' ||
                                    style.visibility === 'hidden'
                            );
                        },
                        debounce : function (fn, delay) {
                          var timer = null;
                          return function () {
                            var context = this, args = arguments;
                            clearTimeout(timer);
                            timer = setTimeout(function () {
                                fn.apply(context, args);
                            }, delay);
                          };
                        },
                        submitResponse: function(response) {
                            if (typeof gpyload.observer !== 'undefined') {
                                gpyload.observer.disconnect();
                            }
                            var responseMessage = {actionCode: "pyloadSubmitResponse", params: {response: response}};
                            parent.postMessage(JSON.stringify(responseMessage),"*");
                        },
                        activated: function() {
                            var responseMessage = {actionCode: "pyloadActivatedInteractive"};
                            parent.postMessage(JSON.stringify(responseMessage),"*");
                        },
                        setSize : function(rect) {
                            if (gpyload.data.rectDoc.left !== rect.left || gpyload.data.rectDoc.right !== rect.right || gpyload.data.rectDoc.top !== rect.top || gpyload.data.rectDoc.bottom !== rect.bottom) {
                                gpyload.data.rectDoc = rect;
                                var responseMessage = {actionCode: "pyloadIframeSize", params: {rect: rect}};
                                parent.postMessage(JSON.stringify(responseMessage), "*");
                            }
                        },
                        data : {
                            debounceInterval: 1500,
                            rectDoc: {top: 0, right: 0, bottom: 0, left: 0}
                        }
                    };

                    try {
                        eval(request.params.script.code);
                    } catch(err) {
                        console.error("pyLoad: Script aborted: " + err.name + ": " + err.message + " (" + err.stack +")");
                        return;
                    }
                    if (typeof gpyload.getFrameSize === "function") {
                        var checkDocSize = gpyload.debounce(function() {
                            window.scrollTo(0,0);
                            var rect = gpyload.getFrameSize();
                            gpyload.setSize(rect);
                        }, gpyload.data.debounceInterval);
                        gpyload.observer = new MutationObserver(function(mutationsList) {
                            checkDocSize();
                        });
                        var js_script = document.createElement("script");
                        js_script.type = "text/javascript";
                        js_script.innerHTML = "gpyload.observer.observe(document.querySelector('body'), {attributes:true, attributeOldValue:false, characterData:true, characterDataOldValue:false, childList:true, subtree:true});";
                        document.getElementsByTagName('body')[0].appendChild(js_script);
                    }
                } else {
                    console.error("pyLoad: Script signature verification failed")
                }
            }
        }
    });
})();