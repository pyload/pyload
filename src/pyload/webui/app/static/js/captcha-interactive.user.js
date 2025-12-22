// ==UserScript==
// @name         pyLoad Script for Interactive Captcha
// @namespace    https://pyload.net/
// @version      0.21
// @author       Michi-F, GammaC0de
// @description  pyLoad Script for Interactive Captcha
// @match        *://*/*
// @homepage     https://github.com/pyload/pyload
// @icon         https://raw.githubusercontent.com/pyload/pyload/main/src/pyload/webui/app/static/img/favicon.ico
// @updateURL    https://raw.githubusercontent.com/pyload/pyload/main/src/pyload/webui/app/static/js/captcha-interactive.user.js
// @downloadURL  https://raw.githubusercontent.com/pyload/pyload/main/src/pyload/webui/app/static/js/captcha-interactive.user.js
// @supportURL   https://github.com/pyload/pyload/issues
// @grant        GM_setValue
// @grant        GM_getValue
// @grant        GM_registerMenuCommand
// @grant        GM_notification
// @run-at       document-start
// @require      https://kjur.github.io/jsrsasign/jsrsasign-all-min.js
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

(function () {
  "use strict";

  // Settings storage abstraction
  class SettingsStore {
    constructor() {
      this._modified = false;
      this.settings = {
        trustedOrigins: [], // array of trusted parent origins
        initialShow: true // whether to show the settings panel on first run
      };
      this.load();
    }
    get(key) {
      return this.settings[key];
    }
    set(key, value) {
      this.settings[key] = value;
      this._modified = true;
    }
    load() {
      for (const key of Object.keys(this.settings)) {
        const value = GM_getValue(key, this.settings[key]);
        if (value === this.settings[key]) {
          this.save(key); // save default if not present
        }
        this.settings[key] = value;
      }
      this._modified = false;
    }
    save(key= null) {
      if (key !== null) {
        // Save single setting
        GM_setValue(key, this.settings[key]);
      } else {
        // Save all settings
        for (const [key, value] of Object.entries(this.settings)) {
          GM_setValue(key, value);
        }
        this._modified = false;
      }
    }
    modified() {
      return this._modified;
    }
  }

  const settings = new SettingsStore();

  function normalizeOrigin(input) {
    try {
      if (input == null) return null;
      let s = String(input).toLowerCase().trim();
      if (!/^https?:\/\//.test(s)) {
         return null;
      }
      const u = new URL(s);
      return u.origin; // scheme + host + optional port, no trailing slash
    } catch (e) {
      return null;
    }
  }

  // Settings UI class
  class SettingsPanel {
    constructor(settingsStore) {
      this.settings = settingsStore;
      this.host = null;
      this.shadow = null;
      this.panel = null;
      this.listbox = null;
      this._prevBodyOverflow = null;
      this.overlay = null;
      this._promise = null;
      this._resolveFunc = null;
    }

    open() {
      if (this._promise) return this._promise;
      this._promise = new Promise((resolve) => {
        this._resolveFunc = resolve;
        const showPanel = () => {
          if (window.top !== window.self) {
            resolve(null);
            return;
          }

          this.buildUI();
          this.updateListbox();
          this.bindEvents();

          // Focus the new origin input initially while still capturing key events on the panel
          const newOriginInput = this.shadow.querySelector("#newOrigin");
          newOriginInput.focus({ preventScroll: true });
          newOriginInput.select?.();
        };

        if (!document.body) {
          document.addEventListener("DOMContentLoaded", showPanel, { once: true });
        } else {
          showPanel();
        }
      });
      return this._promise;
    }

    close(returnVal = false) {
      if (this._prevBodyOverflow !== null) {
        document.body.style.overflow = this._prevBodyOverflow;
        this._prevBodyOverflow = null;
      }

      // Detach key event boundary listeners
      if (this._stopKeyEventPropagation && this.host) {
        ["keydown", "keyup", "keypress"].forEach((type) => {
          this.host.removeEventListener(type, this._stopKeyEventPropagation, true);
          this.host.removeEventListener(type, this._stopKeyEventPropagation, false);
        });
        this._stopKeyEventPropagation = null;
      }

      if (this.host) {
        this.host.remove();
        this.host = null;
        this.shadow = null;
        this.panel = null;
        this.listbox = null;
        this.overlay = null;
      }

      if (returnVal === false) {
        // If the panel is closed without saving, revert unsaved changes
        this.settings.load();
      } else {
        this.settings.save();
      }
      if (this._resolveFunc) {
        try {
          this._resolveFunc(returnVal);
        } catch (e) { /* no-op */ }
      }
      this._promise = null;
      this._resolveFunc = null;
    }

    buildUI() {
      // Create a host element for the shadow DOM
      this.host = document.createElement("div");
      document.body.appendChild(this.host);
      this.host.style.position = "fixed";
      this.host.style.zIndex = "2147483647";
      this.host.style.left = "0";
      this.host.style.top = "0";

      // Attach shadow DOM (closed for better encapsulation)
      this.shadow = this.host.attachShadow({ mode: "closed", delegatesFocus: true });
      this._prevBodyOverflow = document.body.style.overflow;
      document.body.style.overflow = "hidden";

      // Create settings panel
      this.panel = document.createElement("div");
      // enforce left-to-right layout inside the panel
      this.panel.dir = "ltr";
      this.panel.setAttribute("role", "dialog");
      this.panel.setAttribute("aria-modal", "true");
      this.panel.setAttribute("aria-label", "pyLoad Interactive Captcha Settings");
      this.panel.style.position = "fixed";
      this.panel.style.top = "50%";
      this.panel.style.left = "50%";
      this.panel.style.transform = "translate(-50%, -50%)";
      this.panel.style.background = "#fff";
      this.panel.style.padding = "20px";
      this.panel.style.border = "1px solid #000";
      this.panel.style.zIndex = "1000";
      this.panel.style.maxWidth = "400px";
      this.panel.style.boxShadow = "0 0 10px rgba(0,0,0,0.3)";

      this.panel.innerHTML = `
                <style>
                    :host {
                        all: initial; /* Reset inherited styles */
                        font-family: Arial, sans-serif;
                    }
                    .content {
                        direction: ltr;
                    }
                    .titlebar {
                        display: flex;
                        align-items: center;
                        justify-content: space-between;
                        height: 32px;
                        background: #0078d4; /* Windows 10 accent */
                        color: #fff;
                        padding: 0 8px;
                        user-select: none;
                        cursor: default;
                        margin: -20px -20px 10px -20px; /* extend over panel padding */
                        border-bottom: 1px solid rgba(0,0,0,0.2);
                    }
                    .titlebar .title {
                        font-size: 13px;
                        font-weight: 600;
                    }
                    .window-controls {
                        display: flex;
                        gap: 2px;
                    }
                    .window-controls button {
                        width: 46px;
                        height: 28px;
                        border: none;
                        background: transparent;
                        color: #fff;
                        font-size: 16px;
                        line-height: 28px;
                        text-align: center;
                        cursor: pointer;
                    }
                    .window-controls button#windowClose:hover {
                        background: #e81123; /* Windows close hover */
                    }
                    h3 {
                        margin: 0 0 10px 0;
                    }
                    .content input, .content select, .content button {
                        font-size: 14px;
                    }
                    .content select {
                        width: 100%;
                        height: 100px;
                    }
                    .content button {
                        padding: 5px 10px;
                        cursor: pointer;
                    }
                    .content label {
                        display: block;
                        margin-bottom: 3px;
                        font-size: 13px;
                    }
                    .content div {
                        margin-bottom: 10px;
                    }
                </style>
                <div class="titlebar">
                    <div class="title">pyLoad Interactive Captcha Settings</div>
                    <div class="window-controls">
                        <button id="windowClose" aria-label="Close" title="Close">×</button>
                    </div>
                </div>
                <div class="content">
                    <h3>Manage pyLoad Origins List</h3>
                    <div>
                        <label for="newOrigin">pyLoad instance URL:</label>
                        <input type="text" id="newOrigin" style="width: 70%; margin-right: 5px;">
                        <button id="addOrigin">Add</button>
                    </div>
                    <div>
                        <label for="originList">Trusted Origins:</label>
                        <select id="originList" size="5"></select>
                    </div>
                    <div>
                        <button id="removeOrigin" style="margin-right: 10px;">Remove Selected</button>
                        <button id="saveSettings">Save</button>
                        <button id="closeSettings">Close</button>
                    </div>
                </div>
            `;
      this.overlay = document.createElement("div");
      this.overlay.style.position = "fixed";
      this.overlay.style.left = "0";
      this.overlay.style.top = "0";
      this.overlay.style.width = "100vw";
      this.overlay.style.height = "100vh";
      this.overlay.style.background = "rgba(0,0,0,0.35)";
      this.overlay.style.zIndex = "900";
      this.overlay.style.pointerEvents = "auto";
      this.shadow.appendChild(this.overlay);
      this.shadow.appendChild(this.panel);

      // Prevent key events from escaping the shadow DOM by stopping propagation
      // at the host boundary (both capture and bubble phases)
      this._stopKeyEventPropagation = (ev) => {
        // Do not preventDefault here so inputs inside the panel retain native behavior
        ev.stopPropagation();
        if (typeof ev.stopImmediatePropagation === "function") ev.stopImmediatePropagation();
      };
      ["keydown", "keyup", "keypress"].forEach((type) => {
        this.host.addEventListener(type, this._stopKeyEventPropagation, true);  // capture
        this.host.addEventListener(type, this._stopKeyEventPropagation, false); // bubble
      });

      // Cache listbox reference
      this.listbox = this.shadow.querySelector("#originList");
    }

    updateListbox() {
      this.listbox.innerHTML = "";
      this.settings.get("trustedOrigins").forEach(str => {
        const option = document.createElement("option");
        option.value = str;
        option.text = str;
        this.listbox.appendChild(option);
      });
    }

    bindEvents() {
      // Add new trusted origin
      const newOriginInput = this.shadow.querySelector("#newOrigin");
      this.shadow.querySelector("#addOrigin").addEventListener("click", () => {
        const newOrigin = newOriginInput.value.trim();
        const normalized = normalizeOrigin(newOrigin);
        if (!normalized) {
          this.showToast("Invalid URL. Please enter a valid http(s) URL including the scheme and optional port (e.g. https://pyload.example.com:8080).", "red", 10000);
          return;
        }
        let trustedOrigins = this.settings.get("trustedOrigins");
        if (!trustedOrigins.includes(normalized)) {
          trustedOrigins.push(normalized);
          this.settings.set("trustedOrigins", trustedOrigins);
          this.updateListbox();
          newOriginInput.value = "";
          requestAnimationFrame(() => newOriginInput.focus({ preventScroll: true }));
        }
      });

      // Remove selected trusted origin
      this.shadow.querySelector("#removeOrigin").addEventListener("click", () => {
        const selectedIndex = this.listbox.selectedIndex;
        if (selectedIndex !== -1) {
          let trustedOrigins = this.settings.get("trustedOrigins")
          trustedOrigins.splice(selectedIndex, 1);
          this.settings.set("trustedOrigins", trustedOrigins);
          this.updateListbox();
        }
      });

      // Save settings
      this.shadow.querySelector("#saveSettings").addEventListener("click", () => {
        this.showToast("Settings saved", "green", 1500).then(() => this.close(true));
      });

      // Close panel button and Title bar close button
      ["#closeSettings", "#windowClose"].forEach((sel) => {
        this.shadow.querySelector(sel).addEventListener("click", () => {
          if (this.settings.modified()) {
            this.showToast("NOT saved", "red", 1500).then(() => this.close(false));
          } else {
            this.close(false)
          }
        });
      });

      // // Close on overlay click
      // if (this.overlay) {
      //   this.overlay.addEventListener("click", () => this.close(false));
      // }

      // Close on Escape key + focus trap
      this.panel.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
          this.close();
          return;
        }
        if (event.key === "Tab") {
          const focusables = this.getFocusableElements();
          if (!focusables.length) return;
          const first = focusables[0];
          const last = focusables[focusables.length - 1];
          const active = event.target;
          if (event.shiftKey) {
            if (active === first) {
              last.focus();
              event.preventDefault();
            }
          } else {
            if (active === last) {
              first.focus();
              event.preventDefault();
            }
          }
        }
      });
    }

    showToast(text, color = "green", duration = 1500) {
      return new Promise((resolve) => {
        const toastDiv = this.shadow.querySelector("#saveStatus");
        if (!toastDiv) {
          const status = document.createElement("div");
          status.id = "saveStatus";
          status.textContent = text;
          status.style.color = color;
          this.panel.appendChild(status);
          setTimeout(() => {
            if (status.parentNode) status.parentNode.removeChild(status);
            resolve();
          }, duration);
        } else {
          setTimeout(() => {
            resolve();
          }, duration);
        }
      });
    }

    getFocusableElements() {
      if (!this.panel) return [];
      const selectors = [
        "a[href]", "area[href]", "input:not([disabled])", "select:not([disabled])",
        "textarea:not([disabled])", "button:not([disabled])", '[tabindex]:not([tabindex="-1"])'
      ];
      return Array.from(this.panel.querySelectorAll(selectors.join(",")));
    }
  }

   if (window.top === window.self) {
    // Register menu command to open settings (top-level only)
    GM_registerMenuCommand("Open pyLoad Interactive Captcha Settings", showSettings);

    if (settings.get("initialShow")) {
      showSettings(function (result) {
        if (!result) {
          GM_notification({
            title: "pyLoad Interactive Captcha Script",
            text: "Please configure the script settings before use.\nYou can open the settings later from the user script manager menu."
          });
        }
        // Disable initial show on subsequent runs
        settings.set("initialShow", false);
        settings.save("initialShow");
      });
    }
  }

  function showSettings(callback=null) {
    if (window.top !== window.self) return;

    const ui = new SettingsPanel(settings);
    ui.open().then(value => {
      if (typeof callback === "function") callback(value);
    }).catch(() => {
      if (typeof callback === "function") callback(null);
    });
  }

  if (settings.get("trustedOrigins").length > 0) {
    // this function listens to messages from the pyload main page
    window.addEventListener("message", function (ev) {
      // Restrict accepted origins to a trusted set.
      const trustedOrigins = settings.get("trustedOrigins");
      if (!trustedOrigins.includes(ev.origin)) {
        // Ignore messages from untrusted or unknown origins
        return;
      }
      let request;
      try {
        request = JSON.parse(ev.data);
      } catch (e) {
        return;
      }
      if (request && typeof request === "object" && request.actionCode === "pyloadActivateInteractive") {
        if (request.params.script) {
          if (typeof KJUR === "undefined" || typeof KJUR.crypto?.Signature !== "function") {
            console.error("pyLoad: crypto library not available; aborting.");
            return;
          }
          const sig = new KJUR.crypto.Signature({ "alg": "SHA384withRSA", "prov": "cryptojs/jsrsa" });
          sig.init("-----BEGIN PUBLIC KEY-----\n" +
            "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAuEHE4uAeTeEQjIwB//YH\n" +
            "Gl5e058aJRCRyOvApv1iC1ZQgXGHopgEd528+AtkAZKdCRkoNCWda7L/hROpZNjq\n" +
            "xgO5NjjlBnotntQiZ6xr7A4Kfdctmw1DPcv/dkp6SXRpAAw8BE9CctZ3H7cE/4UT\n" +
            "FIJOYQQXF2dcBTWLnUAjesNoHBz0uHTdvBIwJdfdUIrNMI4IYXL4mq9bpKNvrwrb\n" +
            "iNhSqN0yV8sanofZmDX4JUmVGpWIkpX0u+LA4bJlaylwPxjuWyIn5OBED0cdqpbO\n" +
            "7t7Qtl5Yu639DF1eZDR054d9OB3iKZX1a6DTg4C5DWMIcU9TsLDm/JJKGLWRxcJJ\n" +
            "fwIDAQAB\n" +
            "-----END PUBLIC KEY-----");
          sig.updateString(request.params.script.code);
          if (sig.verify(request.params.script.signature)) {
            const gpyload = {
              isVisible: function (element) {
                const style = window.getComputedStyle(element);
                const rect = element.getBoundingClientRect();
                return !(
                  rect.width === 0 ||
                  rect.height === 0 ||
                  style.display === "none" ||
                  style.visibility === "hidden" ||
                  style.opacity === "0"
                );
              },
              debounce: function (fn, delay) {
                let timer = null;
                return function () {
                  const context = this, args = arguments;
                  clearTimeout(timer);
                  timer = setTimeout(function () {
                    fn.apply(context, args);
                  }, delay);
                };
              },
              submitResponse: function (response) {
                if (typeof gpyload.observer !== "undefined") {
                  gpyload.observer.disconnect();
                }
                const responseMessage = { actionCode: "pyloadSubmitResponse", params: { response: response } };
                if (window.parent !== window && gpyload.data.parentOrigin) {
                  parent.postMessage(JSON.stringify(responseMessage), gpyload.data.parentOrigin);
                }
              },
              activated: function () {
                const responseMessage = { actionCode: "pyloadActivatedInteractive" };
                if (window.parent !== window && gpyload.data.parentOrigin) {
                  parent.postMessage(JSON.stringify(responseMessage), gpyload.data.parentOrigin);
                }
              },
              setSize: function (rect) {
                if (gpyload.data.rectDoc.left !== rect.left || gpyload.data.rectDoc.right !== rect.right || gpyload.data.rectDoc.top !== rect.top || gpyload.data.rectDoc.bottom !== rect.bottom) {
                  gpyload.data.rectDoc = rect;
                  const responseMessage = { actionCode: "pyloadIframeSize", params: { rect: rect } };
                  if (window.parent !== window && gpyload.data.parentOrigin) {
                    parent.postMessage(JSON.stringify(responseMessage), gpyload.data.parentOrigin);
                  }
                }
              },
              data: {
                debounceInterval: 1500,
                rectDoc: { top: 0, right: 0, bottom: 0, left: 0 },
                parentOrigin: ev.origin
              }
            };

            try {
              let scriptFunction = new Function("request", "gpyload", '"use strict";' + request.params.script.code);
              scriptFunction(request, gpyload);
            } catch (err) {
              console.error("pyLoad: Script aborted: " + err.name + ": " + err.message + " (" + err.stack + ")");
              return;
            }
            if (typeof gpyload.getFrameSize === "function") {
              const checkDocSize = gpyload.debounce(() => {
                window.scrollTo(0, 0);
                const rect = gpyload.getFrameSize();
                gpyload.setSize(rect);
              }, gpyload.data.debounceInterval);
              gpyload.observer = new MutationObserver(function (mutationsList) {
                checkDocSize();
              });
              const startObserving = function () {
                if (document.body) {
                  gpyload.observer.observe(document.body, {
                    attributes: true,
                    attributeOldValue: false,
                    characterData: true,
                    characterDataOldValue: false,
                    childList: true,
                    subtree: true
                  });
                }
              };
              if (document.readyState === "loading") {
                document.addEventListener("DOMContentLoaded", startObserving, { once: true });
              } else {
                startObserving();
              }
            }
          } else {
            console.error("pyLoad: Script signature verification failed");
          }
        }
      }
    });
  }
})();
