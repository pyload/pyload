#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re

from ..base.captcha_service import CaptchaService


class CoinHive(CaptchaService):
    __name__ = "CoinHive"
    __type__ = "anticaptcha"
    __version__ = "0.01"
    __status__ = "testing"

    __description__ = "CoinHive captcha service plugin"
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    KEY_PATTERN = r'class=[\'"]coinhive-captcha[\'"].+?data-key\s*=[\'"](\w+?)[\'"]'
    HASHES_PATTERN = (
        r'class=[\'"]coinhive-captcha[\'"].+?data-hashes\s*=[\'"](\d+?)[\'"]'
    )

    COINHIVE_INTERACTIVE_SIG = (
        "792398cf130e9cb0d1c16363c87122a623d0bc7410bd981000f5cbfe1c6ec6708d16edf19bc2703b"
        + "04291697cfde5194c5dc290a23b10af5ad6a26606867a5e38031aa24d715c7ec48a5c61272d757a5"
        + "4835e77558933744a3f0ad245a72ea9447893284c4fd458544a9bff09c19b187321ec7b0f1b2b21e"
        + "246bef741b27f3058b2467a192c100b78bb311300e5da0ce95b331bb77215e261fb4a6b78acd89a7"
        + "13aefdc393fb19f3cdb4682b084c5747347f344fd49ed86bad7fba1ad2f059663ff1b800cffa8948"
        + "bb9c12dddf0ae96831b85c4f9526460cd2a4355c4f800aeb4b541b5c5bee62dc5bfb18c6656c0304"
        + "0b2a819edd07480911b6dadf430f6eb1"
    )

    COINHIVE_INTERACTIVE_JS = """
            while(document.children[0].childElementCount > 0) {
                document.children[0].removeChild(document.children[0].children[0]);
            }
            document.children[0].innerHTML = '<html><body><div class="coinhive-captcha"' + (request.params.hashes ? 'data-hashes="' + request.params.hashes +'"' : '') + ' data-key="' + request.params.key +'" data-callback="pyloadCaptchaFinishCallback"><em>Loading Coinhive Captcha...</em></div></body></html>';

            gpyload.getFrameSize = function() {
                var divCoinHive = document.body.querySelector("iframe[src*='authedmine.com/captcha/']");
                if (divCoinHive !== null) {
                    var rect = divCoinHive.getBoundingClientRect();
                    return {top: Math.round(rect.top), right: Math.round(rect.right), bottom: Math.round(rect.bottom), left: Math.round(rect.left)};
                } else {
                    return {top: 0, right: 0, bottom: 0, left: 0};
                };
            };
            window.pyloadCaptchaFinishCallback = function(token){
                gpyload.submitResponse(token);
            }
            var js_script = document.createElement('script');
            js_script.type = "text/javascript";
            js_script.src = "https://authedmine.com/lib/captcha.min.js";
            js_script.async = true;
            document.getElementsByTagName('head')[0].appendChild(js_script);

            gpyload.activated();"""

    def detect_key(self, data=None):
        html = data or self.retrieve_data()

        m = re.search(self.KEY_PATTERN, html)
        if m is not None:
            self.key = m.group(1).strip()
            self.log_debug(f"Key: {self.key}")
            return self.key
        else:
            self.log_warning(self._("Key pattern not found"))
            return None

    def detect_hashes(self, data=None):
        html = data or self.retrieve_data()
        m = re.search(self.HASHES_PATTERN, html)
        if m is not None:
            self.hashes = m.group(1).strip()
            self.log_debug(f"Hashes: {self.hashes}")
            return self.hashes
        else:
            self.log_warning(self._("Hashes pattern not found"))
            return None

    def challenge(self, key=None, hashes=None, data=None):
        key = key or self.retrieve_key(data)
        hashes = hashes or self.detect_hashes(data)
        params = {
            "url": self.pyfile.url,
            "key": key,
            "hashes": hashes,
            "script": {
                "signature": self.COINHIVE_INTERACTIVE_SIG,
                "code": self.COINHIVE_INTERACTIVE_JS,
            },
        }

        result = self.decrypt_interactive(params, timeout=300)

        return result


if __name__ == "__main__":
    # Sign with the command `python -m pyload.plugins.captcha.CoinHive
    # pyload.private.pem pem_passphrase`
    import sys
    from ..helpers import sign_string

    if len(sys.argv) > 2:
        with open(sys.argv[1]) as fp:
            pem_private = fp.read()

        print(
            sign_string(
                CoinHive.COINHIVE_INTERACTIVE_JS,
                pem_private,
                pem_passphrase=sys.argv[2],
                sign_algo="SHA384",
            )
        )
