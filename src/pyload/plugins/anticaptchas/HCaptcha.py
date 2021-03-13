# -*- coding: utf-8 -*-

import re
import urllib.parse

from ..base.captcha_service import CaptchaService

class HCaptcha(CaptchaService):
    __name__ = 'HCaptcha'
    __type__ = 'captcha'
    __version__ = '0.01'
    __status__ = 'testing'

    __description__ = 'hCaptcha captcha service plugin'
    __license__ = 'GPLv3'
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    KEY_PATTERN = r'(?:data-sitekey=["\']|["\']sitekey["\']\s*:\s*["\'])((?:[\w\-]|%[0-9a-fA-F]{2})+)'
    KEY_FORMAT_PATTERN = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'

    HCAPTCHA_INTERACTIVE_SIG = "24f1aba331a2fd110dfe31791c55104beb34e14cd6e4a2d80915e8284ca25384c47375d303ae1457" + \
                               "37cb9af1fa70902d90858a434fe4e9732d85dd9bcc427359dc1e67326cbfebc1b5972a57f07aa47f" + \
                               "ead6fabf1624ee44ab39d53f77bc8903c81b7d8d007228a7f2ba161d7f6a42fea2589c42a4464676" + \
                               "504ed02e1d7ed5f99d35a5b3871d85411098474ba2c135652c889f8f1b7845d75cd5c2b82e58265d" + \
                               "48faf9ed586277d2ac3d7ff2efadff2b89b4082ec0d5d7f688b50b741489fd48e50560c1bd495a1a" + \
                               "d5e24d67e9eb95fa111cd84793807a27bf6d3302493aeaa899036f08c7d8b187c1d14d1ff7a30b77" + \
                               "5cba1e63e87cf829f536a7cff04b6639"

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
				hcaptcha.render (
					"captchadiv",
					{size: "compact",
					 'sitekey': gpyload.data.sitekey,
					 'callback': function() {
						var hcaptchaResponse = hcaptcha.getResponse(); // get captcha response
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
                self.log_debug("Key: %s" % self.key)
                return self.key

            else:
                self.log_debug(key, "Wrong key format, this probably because is is not a hCaptcha key")

        self.log_warning(self._("Key pattern not found"))
        return None

    def challenge(self, key=None, data=None):
        key = key or self.retrieve_key(data)

        return self._challenge_js(key)

    # solve interactive captcha (javascript required)
    def _challenge_js(self, key):
        self.log_debug("Challenge hCaptcha interactive")

        params = {'url': self.pyfile.url,
                  'sitekey': key,
                  'script': {'signature': self.HCAPTCHA_INTERACTIVE_SIG,
                             'code': self.HCAPTCHA_INTERACTIVE_JS}}

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
