# -*- coding: utf-8 -*-

from __future__ import with_statement

import os
import re
import urllib
import urlparse
from StringIO import StringIO

from ..internal.CaptchaService import CaptchaService

try:
    no_pil = False
    from PIL import Image
    from PIL import ImageDraw
    from PIL import ImageFont

except ImportError:
    try:
        import Image
        import ImageDraw
        import ImageFont

    except ImportError:
        no_pil = True


class ReCaptcha(CaptchaService):
    __name__ = 'ReCaptcha'
    __type__ = 'captcha'
    __version__ = '0.43'
    __status__ = 'testing'

    __description__ = 'ReCaptcha captcha service plugin'
    __license__ = 'GPLv3'
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com"),
                   ("zapp-brannigan", "fuerst.reinje@web.de"),
                   ("Arno-Nymous", None),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    KEY_V2_PATTERN = r'(?:data-sitekey=["\']|["\']sitekey["\']\s*:\s*["\'])((?:[\w\-]|%[0-9a-fA-F]{2})+)'

    STOKEN_V2_PATTERN = r'data-stoken=["\']([\w\-]+)'

    RECAPTCHA_INTERACTIVE_SIG = "7b99386315b3e035285946b842049575fc69a88ccc219e1bc96a9afd0f3c4b7456f09d36bf3dc530" + \
                                "a08cd50f1b3128716cf727b30f7de4ab1513f15bb82776e84404089a764c6305d9c6033c99f8514e" + \
                                "249bc3fd5530b475c00059797ce5a45d131adb626a440366af9acc9a50a3a7327b9d3dc28b59f83f" + \
                                "32129feb89e0cfb74521c306e8ac0b9fff9df31d453eedc54a17d41528c2d866363fc13cb524ad77" + \
                                "60483b28bf4a347de4a8b2b1480f83f66c4408ad9dbfec78f6f1525b8507b6e52cdd13e13f8e3bfc" + \
                                "0bb5dd1860e6fc5db99ef0c915fd626c3aaec0bb5ead3a668ebb31dd2a08eacaefffdf51e3a0ba31" + \
                                "cb636da134c24633f2b2b38f56dfbb92"

    RECAPTCHA_INTERACTIVE_JS = """
			while(document.children[0].childElementCount > 0) {
				document.children[0].removeChild(document.children[0].children[0]);
			}
			document.children[0].innerHTML = '<html><head></head><body style="display:inline-block;"><div id="captchadiv" style="display: inline-block;"></div></body></html>';

			gpyload.data.sitekey = request.params.sitekey;

			gpyload.getFrameSize = function() {
				var rectAnchor =  {top: 0, right: 0, bottom: 0, left: 0},
					rectPopup =  {top: 0, right: 0, bottom: 0, left: 0},
					rect;
				var anchor = document.body.querySelector("iframe[src*='/anchor']");
				if (anchor !== null && gpyload.isVisible(anchor)) {
					rect = anchor.getBoundingClientRect();
					rectAnchor = {top: rect.top, right: rect.right, bottom: rect.bottom, left: rect.left};
				}
				var popup = document.body.querySelector("iframe[src*='/bframe']");
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
				grecaptcha.render (
					"captchadiv",
					{size: "compact",
					 'sitekey': gpyload.data.sitekey,
					 'callback': function() {
						var recaptchaResponse = grecaptcha.getResponse(); // get captcha response
						gpyload.submitResponse(recaptchaResponse);
					 }}
				);
				gpyload.activated();
			};

			if(typeof grecaptcha !== 'undefined' && grecaptcha) {
				window.pyloadCaptchaOnLoadCallback();
			} else {
				var js_script = document.createElement('script');
				js_script.type = "text/javascript";
				js_script.src = "//www.google.com/recaptcha/api.js?onload=pyloadCaptchaOnLoadCallback&render=explicit";
				js_script.async = true;
				document.getElementsByTagName('head')[0].appendChild(js_script);
			}"""

    def detect_key(self, data=None):
        html = data or self.retrieve_data()

        m = re.search(self.KEY_V2_PATTERN, html)
        if m is not None:
            self.key = urllib.unquote(m.group(1).strip())
            self.log_debug("Key: %s" % self.key)
            return self.key
        else:
            self.log_warning(_("Key pattern not found"))
            return None

    def detect_secure_token(self, data=None):
        html = data or self.retrieve_data()

        m = re.search(self.STOKEN_V2_PATTERN, html)
        if m is not None:
            self.secure_token = m.group(1).strip()
            self.log_debug("Secure Token: %s" % self.secure_token)
            return self.secure_token
        else:
            self.log_warning(_("Secure Token pattern not found"))
            return None

    def detect_version(self, data=None):
        data = data or self.retrieve_data()

        v2 = re.search(self.KEY_V2_PATTERN, data) is not None

        if v2 is True:
            self.log_debug("Detected reCAPTCHA v2")
            return 2

        else:
            self.log_warning(_("Could not properly detect reCAPTCHA version, defaulting to v2"))
            return 2

    def challenge(self, key=None, data=None, version=None, secure_token=None):
        key = key or self.retrieve_key(data)
        secure_token = secure_token or self.detect_secure_token(data) if secure_token is not False else None

        if version in (2, '2js'):
            return getattr(self, "_challenge_v%s" % version)(key, secure_token=secure_token)
        else:
            return self.challenge(key,
                                  data,
                                  version=self.detect_version(data=data),
                                  secure_token=secure_token)

    def _prepare_image(self, image, challenge_msg):
        if no_pil:
            self.log_error(
                _("Missing PIL lib"),
                _("Please install python's PIL library"))
            self.fail(_("Missing PIL lib"))

        dummy_text = 'pk'
        # This is just a string to calculate biggest height of a text, since usually
        # the letters 'p' and 'k' reach to the lower most respective higher most
        # points in a text font (see typography) and thus we can hereby calculate
        # the biggest text height of a given font

        s = StringIO()
        s.write(image)
        s.seek(0)

        img = Image.open(s)
        draw = ImageDraw.Draw(img)

        font_name = 'arialbd'

        if os.name == 'nt':
            font = ImageFont.truetype(font_name, 13)
        else:
            font = None

        tile_size = {'width': img.size[0] / 3, 'height': img.size[1] / 3}
        tile_index_size = {
            'width': draw.textsize('0')[0],
            'height': draw.textsize('0')[1]}

        margin = 2
        for x in range(3):
            for y in range(3):
                tile_index_pos = {
                    'x': x * tile_size['width'] + (tile_size['width'] / 2) - (tile_index_size['width'] / 2),
                    'y': y * tile_size['height']
                }

                draw.rectangle(
                    [
                        tile_index_pos['x'] - margin,
                        tile_index_pos['y'],
                        tile_index_pos['x'] +
                        tile_index_size['width'] + margin,
                        tile_index_pos['y'] + tile_index_size['height']
                    ],
                    fill='white'
                )

                index_number = str(y * 3 + x + 1)
                text_width, text_height = draw.textsize(index_number, font=font)

                draw.text(
                    (
                        tile_index_pos['x'] + (tile_index_size['width'] / 2) - (text_width / 2),
                        tile_index_pos['y'] + (tile_index_size['height'] / 2) - (text_height / 2)
                    ),
                    index_number,
                    '#000',
                    font=font
                )

        if os.name == 'nt':
            font = ImageFont.truetype(font_name, 16)

        _sol = 0
        _eol = 1
        while True:
            # determine maximum width of line
            while draw.textsize(challenge_msg[_sol:_eol], font=font)[
                    0] < img.size[0] and _eol < len(challenge_msg):
                _eol += 1

            # if we've wrapped the text, then adjust the wrap to the last word
            if _eol < len(challenge_msg):
                _eol = challenge_msg.rfind(" ", 0, _eol)
                if _eol > 0:
                    challenge_msg = challenge_msg[
                        :_eol] + '\n' + challenge_msg[_eol + 1:]
                    _sol = _eol + 1
            else:
                break

        message = challenge_msg + '\n(Type image numbers like "258")'

        # the text's real height is twice as big as returned by font.getsize() since we use
        # a newline character which indeed breaks the text but doesn't count as a second line
        # in font.getsize().
        if os.name == 'nt':
            text_area_height = draw.multiline_textsize(message, font=font)[1]

        else:
            lines = message.split('\n')
            text_area_height = len(lines) * draw.textsize(dummy_text, font=font)[1]

        margin = 5
        text_area_height = text_area_height + margin * \
            2  # add some margin on top and bottom of text

        img2 = Image.new('RGB', (img.size[0], img.size[1] + text_area_height), 'white')
        img2.paste(img, (0, text_area_height))
        draw = ImageDraw.Draw(img2)

        if os.name == 'nt':
            draw.text((3, margin), message, fill='black', font=font)
        else:
            for i in range(len(lines)):
                draw.text((3, i * draw.textsize(dummy_text, font=font)[1] + margin),
                          lines[i],
                          fill='black',
                          font=font)

        s.truncate(0)
        img2.save(s, format='JPEG')
        img = s.getvalue()
        s.close()

        return img

    def _challenge_v2(self, key, secure_token=None):
        fallback_url = "https://www.google.com/recaptcha/api/fallback?k=" + key \
                       + ("&stoken=" + secure_token if secure_token else "")

        html = self.pyfile.plugin.load(fallback_url, ref=self.pyfile.url)

        if re.search(r'href="https://support.google.com/recaptcha.*"', html) is not None:
            self.log_warning(_("reCAPTCHA noscript is blocked, trying reCAPTCHA interactive"))
            return self._challenge_v2js(key, secure_token=secure_token)

        for i in range(10):
            try:
                challenge = re.search(r'name="c"\s+value=\s*"([^"]+)', html).group(1)

            except (AttributeError, IndexError):
                self.fail(_("reCAPTCHA challenge pattern not found"))

            try:
                challenge_msg = re.search(r'<label .*?class="fbc-imageselect-message-text">(.*?)</label>',
                                          html).group(1)

            except (AttributeError, IndexError):
                try:
                    challenge_msg = re.search(r'<div .*?class=\"fbc-imageselect-message-error\">(.*?)</div>',
                                              html).group(1)

                except (AttributeError, IndexError):
                    self.fail(_("reCAPTCHA challenge message not found"))

            challenge_msg = re.sub(r'<.*?>', "", challenge_msg)

            image_url = urlparse.urljoin('https://www.google.com',
                                         re.search(r'"(/recaptcha/api2/payload[^"]+)', html).group(1))

            img = self.pyfile.plugin.load(image_url, ref=fallback_url, decode=False)

            img = self._prepare_image(img, challenge_msg)

            response = self.decrypt_image(img)

            post_str = "c=" + urllib.quote_plus(challenge) +\
                       "".join("&response=%s" % str(int(k) - 1)
                               for k in response if k.isdigit())
            html = self.pyfile.plugin.load(fallback_url, post=post_str, ref=fallback_url)

            try:
                result = re.search(r'<div class="fbc-verification-token"><textarea .*readonly>(.*?)</textarea>', html).group(1)
                self.correct()
                break

            except (AttributeError, IndexError):
                self.invalid()

        else:
            self.fail(_("reCAPTCHA max retries exceeded"))

        return result, challenge
    
    # solve interactive captcha (javascript required), use when non-JS captcha fallback for v2 is not allowed
    def _challenge_v2js(self, key, secure_token=None):
        self.log_debug("Challenge reCAPTCHA v2 interactive")

        params = {'url': self.pyfile.url,
                  'sitekey': key,
                  'securetoken': secure_token,
                  'script': {'signature': self.RECAPTCHA_INTERACTIVE_SIG,
                             'code': self.RECAPTCHA_INTERACTIVE_JS}}

        result = self.decrypt_interactive(params, timeout=300)

        return result, result

if __name__ == "__main__":
    # Sign with the command `python -m module.plugins.captcha.ReCaptcha pyload.private.pem pem_passphrase`
    import sys
    from ..internal.misc import sign_string

    if len(sys.argv) > 2:
        with open(sys.argv[1], 'r') as f:
            pem_private = f.read()

        print sign_string(ReCaptcha.RECAPTCHA_INTERACTIVE_JS, pem_private, pem_passphrase=sys.argv[2], sign_algo="SHA384")
