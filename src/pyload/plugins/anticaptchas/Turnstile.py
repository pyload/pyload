# -*- coding: utf-8 -*-

import re
import urllib.parse

from ..base.captcha_service import CaptchaService


class Turnstile(CaptchaService):
    __name__ = "Turnstile"
    __type__ = "anticaptcha"
    __version__ = "0.01"
    __status__ = "testing"

    __description__ = "Turnstile captcha service plugin"
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    KEY_PATTERN = r'(?:data-sitekey=["\']|["\']sitekey["\']\s*:\s*["\'])((?:[\w\-]|%[0-9a-fA-F]{2})+)'
    KEY_FORMAT_PATTERN = r'^0x[0-9a-zA-Z]{22}$'

    TURNSTILE_INTERACTIVE_SIG = "a517150c6b790444f3023e3ac8c2b862af12f261f6e2c569fc3774005f253a94bdec248c2da2742" + \
                                "95ae6f390f420d29fdabf6cded436c87030062d6f4fce45a12b155a4c3ec1c533b630b706f0dbe6" + \
                                "8e14f535fb5f1ed7284db21492f5b4ab17c16e0c0b66b89f011cb5344bb3e6572fd79247fe58a58" + \
                                "f6186633d0a604dfb35985fe9c67845b242d497a367249e48e0cca971fecbe5c3738d4d6ab81f57" + \
                                "bcdc5637fba3fa7d05f5daf86338947116009e443c4cf3ab1071e0f7a371c086ec589cc03727ebc" + \
                                "875b6e6edf715d4b47feb2fadbc80d30c01a6b985b46e600bc6faf89330837681b27d4b018bded4" + \
                                "e0b40ffaea19a62e34bbef294d864db5616e09"

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
                      var turnstileResponse = turnstile.getResponse(widgetID); // get captcha response
                      console.log(`turnstileToken=${turnstileToken}, turnstileResponse=${turnstileResponse}`);
                      gpyload.submitResponse(turnstileResponse);
                  }
              }
            );
            gpyload.activated();
          };

          if(typeof turnstile !== 'undefined' && turnstile) {
            window.pyloadCaptchaOnLoadCallback();
          } else {
            var js_script = document.createElement('script');
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
