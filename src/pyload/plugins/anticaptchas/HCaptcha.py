# -*- coding: utf-8 -*-

import re
import urllib.parse

from ..base.captcha_service import CaptchaService


class HCaptcha(CaptchaService):
    __name__ = "HCaptcha"
    __type__ = "anticaptcha"
    __version__ = "0.02"
    __status__ = "testing"

    __description__ = "hCaptcha captcha service plugin"
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    KEY_PATTERN = r'(?:data-sitekey=["\']|["\']sitekey["\']\s*:\s*["\'])((?:[\w\-]|%[0-9a-fA-F]{2})+)'
    KEY_FORMAT_PATTERN = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'

    HCAPTCHA_INTERACTIVE_SIG = "9ba5840a96ad0503f445c33bddda5ec338c7785ffe27adb680fdb56ee241a9f2b1a3f648ffda0e82" + \
                               "946a683bf9b43780f13d1690cdbca082e5c01deccb05a5d64f8cb84eb8beadf49107ad23da1b2317" + \
                               "2a309fb78403ab3c0ed7019d1383978f2134b62f8d13ab28ebc4164de62b1f29080e31634b3da294" + \
                               "0e7fc604e892ef4726baa672868e88c9600755e72beb674b7e36373febc9b7a0c1508ad7aeaa4c34" + \
                               "79742d3bd71d706bc31b0b2b3d0d94858a28fd4ab0601ebeca4e1e4f0b2a0da395fcaf4c4e5c15b9" + \
                               "4c8f6988f36029d3722d7e0767d141ce45c56d861cfc9a97c93a5817d7b764aaa9309af31b2b0528" + \
                               "f714f7b179d326a303e17a381e99b8d0"

    HCAPTCHA_INTERACTIVE_JS = """
			while(document.children[0].childElementCount > 0) {
				document.children[0].removeChild(document.children[0].children[0]);
			}
			document.children[0].innerHTML = '<html><head></head><body style="display:inline-block;"><div id="captchadiv" style="display: inline-block;"></div></body></html>';

			gpyload.data.sitekey = request.params.sitekey;

			gpyload.getFrameSize = function() {
				var rectAnchor =  {top: 0, right: 0, bottom: 0, left: 0},
					rectPopup =  {top: 0, right: 0, bottom: 0, left: 0},
					rect;
				var anchor = document.body.querySelector("iframe[src*='/hcaptcha-challenge.html']");
				if (anchor !== null && gpyload.isVisible(anchor)) {
					rect = anchor.getBoundingClientRect();
					rectAnchor = {top: rect.top, right: rect.right, bottom: rect.bottom, left: rect.left};
				}
				var popup = document.body.querySelector("iframe[src*='/hcaptcha-checkbox.html']");
				if (popup !== null && gpyload.isVisible(popup)) {
					rect = popup.getBoundingClientRect();
					rectPopup = {top: rect.top, right: rect.right, bottom: rect.bottom, left: rect.left};
				}
				var left = Math.round(Math.min(rectAnchor.left, rectAnchor.right, rectPopup.left, rectPopup.right));
				var right = Math.round(Math.max(rectAnchor.left, rectAnchor.right, rectPopup.left, rectPopup.right));
				var top = Math.round(Math.min(rectAnchor.top, rectAnchor.bottom, rectPopup.top, rectPopup.bottom));
				var bottom = Math.round(Math.max(rectAnchor.top, rectAnchor.bottom, rectPopup.top, rectPopup.bottom));
				return {top: top, left: left, bottom: bottom, right: right};
			};

			// function that is called when the captcha finished loading and is ready to interact
			window.pyloadCaptchaOnLoadCallback = function() {
				var widgetID = hcaptcha.render (
					"captchadiv",
					{size: "compact",
					 'sitekey': gpyload.data.sitekey,
					 'callback': function() {
						var hcaptchaResponse = hcaptcha.getResponse(widgetID); // get captcha response
						gpyload.submitResponse(hcaptchaResponse);
					 }}
				);
				gpyload.activated();
			};

			if(typeof hcaptcha !== 'undefined' && hcaptcha) {
				window.pyloadCaptchaOnLoadCallback();
			} else {
				var js_script = document.createElement('script');
				js_script.type = "text/javascript";
				js_script.src = "//hcaptcha.com/1/api.js?onload=pyloadCaptchaOnLoadCallback&render=explicit";
				js_script.async = true;
				document.getElementsByTagName('head')[0].appendChild(js_script);
			}"""

    def detect_key(self, data=None):
        html = data or self.retrieve_data()

        m = re.search(self.KEY_PATTERN, html)
        if m is not None:
            key = urllib.parse.unquote(m.group(1).strip())
            m = re.search(self.KEY_FORMAT_PATTERN, key)
            if m is not None:
                self.key = key
                self.log_debug("Key: {}".format(self.key))
                return self.key

            else:
                self.log_debug(
                    key,
                    "Wrong key format, this probably because it is not a hCaptcha key",
                )

        self.log_warning(self._("Key pattern not found"))
        return None

    def challenge(self, key=None, data=None):
        key = key or self.retrieve_key(data)

        return self._challenge_js(key)

    # solve interactive captcha (javascript required)
    def _challenge_js(self, key):
        self.log_debug("Challenge hCaptcha interactive")

        params = {
            "url": self.pyfile.url,
            "sitekey": key,
            "script": {
                "signature": self.HCAPTCHA_INTERACTIVE_SIG,
                "code": self.HCAPTCHA_INTERACTIVE_JS,
            },
        }

        result = self.decrypt_interactive(params, timeout=300)

        return result


if __name__ == "__main__":
    # Sign with the command `python -m pyload.plugins.anticaptchas.HCaptcha pyload.private.pem pem_passphrase`
    import sys
    from ..helpers import sign_string

    if len(sys.argv) > 2:
        with open(sys.argv[1]) as fp:
            pem_private = fp.read()

        print(
            sign_string(
                HCaptcha.HCAPTCHA_INTERACTIVE_JS,
                pem_private,
                pem_passphrase=sys.argv[2],
                sign_algo="SHA384",
            )
        )
