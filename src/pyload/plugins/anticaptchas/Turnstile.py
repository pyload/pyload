# -*- coding: utf-8 -*-

import re
import urllib.parse

from ..base.captcha_service import CaptchaService


class Turnstile(CaptchaService):
    __name__ = "Turnstile"
    __type__ = "anticaptcha"
    __version__ = "0.02"
    __status__ = "testing"

    __description__ = "Turnstile captcha service plugin"
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    KEY_PATTERN = r'(?:data-sitekey=["\']|["\']sitekey["\']\s*:\s*["\'])((?:[\w\-]|%[0-9a-fA-F]{2})+)'
    KEY_FORMAT_PATTERN = r'^0x[0-9a-zA-Z\-_]{22}$'

    TURNSTILE_INTERACTIVE_SIG = "779b06997b45a7e8faa47641544530cace0fa1dd6455c4a079a7c0abd7dd981de159e5f8efe43ba" + \
                                "234f49fc3f6c8f3404026c6bceda79a66cb07b75ac256404bc903e9d44574a861ba1153f79f31d4" + \
                                "7af6c27c002d403760419e02917addd29573c7fb3f51996051f7378df2a373746ec6ddd7f704817" + \
                                "35483ff38308fc036f211d11345d0fa560f04e9cb024d4ea76b0c569f7e3116cd0b3d52b64e8e3e" + \
                                "2fe04454c799be5cd3d620d9f00489d43a22b6c621c6de39b20f3ed1f4b9f8bdbf43866d6e90568" + \
                                "c2747ca006536e9f913f2c60d8e3a45fa2014f87ffe9202d94da70dbca7e83917ff58f77e11945c" + \
                                "f7e63f73facb1de766ddcd811ceffc32829425"

    TURNSTILE_INTERACTIVE_JS = """
			while(document.children[0].childElementCount > 0) {
				document.children[0].removeChild(document.children[0].children[0]);
			}
			document.children[0].innerHTML = '<html><head></head><body style="display:inline-block;"><div id="captchadiv" style="display: inline-block;"></div></body></html>';

			gpyload.data.sitekey = request.params.sitekey;

			gpyload.getFrameSize = function() {
				const rectAnchor =  {top: 0, left: 0, right: 150, bottom: 140};
				return rectAnchor;
			};

          // function that is called when the captcha finished loading and is ready to interact
          window.pyloadCaptchaOnLoadCallback = function() {
            const widgetID = turnstile.render (
              "#captchadiv", {
                  size: "compact",
                  'sitekey': gpyload.data.sitekey,
                  'callback': function(turnstileToken) {
                      const turnstileResponse = turnstile.getResponse(widgetID); // get captcha response
                      gpyload.submitResponse(turnstileResponse);
                  }
              }
            );
            gpyload.activated();
          };

          if(typeof turnstile !== 'undefined' && turnstile) {
            window.pyloadCaptchaOnLoadCallback();
          } else {
            const js_script = document.createElement('script');
            js_script.type = "text/javascript";
            js_script.src = "//challenges.cloudflare.com/turnstile/v0/api.js?onload=pyloadCaptchaOnLoadCallback";
            js_script.defer = true;
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
                    "Wrong key format, this probably because it is not a Turnstile key",
                )

        self.log_warning(self._("Key pattern not found"))
        return None

    def challenge(self, key=None, data=None):
        key = key or self.retrieve_key(data)

        return self._challenge_js(key)

    # solve interactive captcha (javascript required)
    def _challenge_js(self, key):
        self.log_debug("Challenge Turnstile interactive")

        params = {
            "url": self.pyfile.url,
            "sitekey": key,
            "script": {
                "signature": self.TURNSTILE_INTERACTIVE_SIG,
                "code": self.TURNSTILE_INTERACTIVE_JS,
            },
        }

        result = self.decrypt_interactive(params, timeout=300)

        return result


if __name__ == "__main__":
    # Sign with the command `python -m pyload.plugins.anticaptchas.Turnstile pyload.private.pem pem_passphrase`
    import sys
    from ..helpers import sign_string

    if len(sys.argv) > 2:
        with open(sys.argv[1]) as fp:
            pem_private = fp.read()

        print(
            sign_string(
                Turnstile.TURNSTILE_INTERACTIVE_JS,
                pem_private,
                pem_passphrase=sys.argv[2],
                sign_algo="SHA384",
            )
        )
