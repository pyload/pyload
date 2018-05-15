# -*- coding: utf-8 -*-

import re

from ..internal.CaptchaService import CaptchaService

class CoinHive(CaptchaService):
    __name__ = 'CoinHive'
    __type__ = 'captcha'
    __version__ = '0.01'
    __status__ = 'testing'

    __description__ = 'CoinHive captcha service plugin'
    __license__ = 'GPLv3'
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    KEY_PATTERN = r'class=[\'"]coinhive-captcha[\'"].+?data-key\s*=[\'"](\w+?)[\'"]'
    HASHES_PATTERN = r'class=[\'"]coinhive-captcha[\'"].+?data-hashes\s*=[\'"](\w+?)[\'"]'

    COINHIVE_INTERACTIVE_SIG = "8034394f54542d58e938637dc70c4ccd5c11eb835ee575bb15e1b77fe2d938e1ef40487b74bbb8b9" + \
                               "fc98b899004e5763af9a3a29ec6eb8fa3aaf6757b64452563e2104c6a98884a66ecb49c4448e32c8" + \
                               "7ddc048fdd2b03c89f8c19f37c9325ed76b21d5a316f33e70b8f6d4f423d1fc5eb678edf2578658d" + \
                               "95846b965540182b1c6111be825289187e492c89d1dc1ae7b030decdc23437833e6235c42396ed1c" + \
                               "64825cef5ba233ccd2a50d45cdd4e07c325fe0068d83b13d098bb481ebe77dff3cb386ab37e97702" + \
                               "5d99d0eaee8055e73e5ba4b07fef25bf9a3d0e4acc2d928c19c94a6deae62f770875905db114282a" + \
                               "99410fb8807834b07670183aa4356525"

    COINHIVE_INTERACTIVE_JS = """
            while(document.children[0].childElementCount > 0) {
                document.children[0].removeChild(document.children[0].children[0]);
            }
            document.children[0].innerHTML = '<html><body><div class="coinhive-captcha"' + (request.params.hashes ? 'data-hashes="' + request.params.hashes +'"' : '') + ' data-key="' + request.params.key +'" data-callback="pyloadCaptchaFinishCallback"><em>Loading Coinhive Captcha...</em></div></body></html>';

            window.pyloadCaptchaFinishCallback = function(token){
                var responseMessage = {actionCode: gpyload.actionCodes.submitResponse, response: token};
                parent.postMessage(JSON.stringify(responseMessage),"*");
            }
            var js_script = document.createElement('script');
            js_script.type = "text/javascript";
            js_script.src = "https://authedmine.com/lib/captcha.min.js";
            js_script.async = true;
            document.getElementsByTagName('head')[0].appendChild(js_script);

            var responseMessage = {actionCode: gpyload.actionCodes.activated};
            parent.postMessage(JSON.stringify(responseMessage),"*");"""

    def detect_key(self, data=None):
        html = data or self.retrieve_data()

        m = re.search(self.KEY_PATTERN, html)
        if m is not None:
            self.key = m.group(1).strip()
            self.log_debug("Key: %s" % self.key)
            return self.key
        else:
            self.log_warning(_("Key pattern not found"))
            return None

    def detect_hashes(self, data=None):
        html = data or self.retrieve_data()
        m = re.search(self.HASHES_PATTERN, html)
        if m is not None:
            self.hashes = m.group(1).strip()
            self.log_debug("Hashes: %s" % self.key)
            return self.hashes
        else:
            self.log_warning(_("Hashes pattern not found"))
            return None

    def challenge(self, key=None, hashes=None, data=None):
        key = key or self.retrieve_key(data)
        hashes = hashes or self.detect_hashes(data)
        params = {'url': self.pyfile.url,
                  'key': key,
                  'hashes': hashes,
                  'script': {'signature': self.COINHIVE_INTERACTIVE_SIG,
                             'code': self.COINHIVE_INTERACTIVE_JS}}

        result = self.decrypt_interactive(params, timeout=300)

        return result

if __name__ == "__main__":
    # Sign with the command `python -m module.plugins.captcha.CoinHive pyload.private.pem pem_passphrase`
    import sys
    from ..internal.misc import sign_string

    if len(sys.argv) > 2:
        with open(sys.argv[1], 'r') as f:
            pem_private = f.read()

        print sign_string(CoinHive.COINHIVE_INTERACTIVE_JS, pem_private, pem_passphrase=sys.argv[2], sign_algo="SHA384")
