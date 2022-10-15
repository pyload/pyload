# -*- coding: utf-8 -*-

import re
import urllib.parse

from ..base.captcha_service import CaptchaService


class HCaptcha(CaptchaService):
    __name__ = "HCaptcha"
    __type__ = "anticaptcha"
    __version__ = "0.03"
    __status__ = "testing"

    __description__ = "hCaptcha captcha service plugin"
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    KEY_PATTERN = r'(?:data-sitekey=["\']|["\']sitekey["\']\s*:\s*["\'])((?:[\w\-]|%[0-9a-fA-F]{2})+)'
    KEY_FORMAT_PATTERN = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'

    HCAPTCHA_INTERACTIVE_SIG = "8595965f0f9fd776231ff65294f515e74384063b64c31d68bdb98ee33a500ab9a5f4ecaf84d24b77" + \
                               "621b516fc8799bbe284e5e6985dcbd6b05dbcb8a5704d75fc566ec8da380ab30d0b65afbd0300169" + \
                               "57432878020c737cee20746c350c79a8888f087041b443e6def2587d9ff6f5ca52a1476dae96c9d1" + \
                               "0d8f3b95edd337a0e8344435a563756eca3b2e4a76fb9581fe265fa8ff6040d1c64180c67798b063" + \
                               "2beb5a8b95f3bc2c16c545bd7335ebaeb9d2fcd654bef7bf51ac1907204eaf9fe1671118c4cf9011" + \
                               "45722303d475f1ab876a75062ba60d17f48da3d2bf795e09749660ce1348a9aeb228eb2129caa565" + \
                               "9268b345ee306113e0c5a2c436cbb0aa"

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
				var anchor = document.body.querySelector("iframe[src*='/hcaptcha.html#frame=checkbox']");
				if (anchor !== null && gpyload.isVisible(anchor)) {
					rect = anchor.getBoundingClientRect();
					rectAnchor = {top: rect.top, right: rect.right, bottom: rect.bottom, left: rect.left};
				}
				var popup = document.body.querySelector("iframe[src*='/hcaptcha.html#frame=challenge']");
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
