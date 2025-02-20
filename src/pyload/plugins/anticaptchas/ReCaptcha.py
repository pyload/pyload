# -*- coding: utf-8 -*-

import io
import os
import re
import urllib.parse

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    pass

from ..base.captcha_service import CaptchaService


class ReCaptcha(CaptchaService):
    __name__ = "ReCaptcha"
    __type__ = "anticaptcha"
    __version__ = '0.51'
    __status__ = "testing"

    __description__ = "ReCaptcha captcha service plugin"
    __license__ = "GPLv3"
    __authors__ = [
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("zapp-brannigan", "fuerst.reinje@web.de"),
        ("Arno-Nymous", None),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    KEY_V2_PATTERN = r'(?:data-sitekey=["\']|["\']sitekey["\']\s*:\s*["\'])((?:[\w\-]|%[0-9a-fA-F]{2})+)'
    KEY_FORMAT_V2_PATTERN = r'^6L[\w-]{6}AAAAA[\w-]{27}$'
    INVISIBLE_V2_PATTERN = r'data-size\s*=\s*(["\'])\s*invisible\s*\1'
    STOKEN_V2_PATTERN = r'data-stoken=["\']([\w\-]+)'

    RECAPTCHA_INTERACTIVE_SIG = "2f33aef5ba02a663108edf83d0e31e991454e6da8ea0fdf8fbc1ba4a3bd70aa3998de5444097c5e9" + \
                                "2972b6b3c3bdb318a21b6241e027508b98434deb7ff1b214b8bbb459e2f4dd0bd603efda09498023" + \
                                "52eef4d280b3e196a602d4c7f05374bc9b71d9d9d232355610512b6299cfcf243b5b5cc5e632b019" + \
                                "6bf62036316c0b335cc69e33d48b6d0d853b3917b681d8ff1a3e3d1b32c97627453345121689ec38" + \
                                "8a89e877ec6ff9e2058f6ffa3c037f5fcb5b5a543a8d9fd2d89b9a400b9dc86eefbd441629ef6313" + \
                                "a1921bf70555c30f378d165b1fb96d52a0810252365af344a965be9e9ab3ac98646e27228e6e4481" + \
                                "8f076d48524a6a4fde517678c4f962ce"

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
				    popup.parentNode.style.width = "";
				    popup.parentNode.style.height = "";
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

			delete window.grecaptcha;
			if(typeof grecaptcha !== 'undefined' && grecaptcha) {
				window.pyloadCaptchaOnLoadCallback();
			} else {
				var js_script = document.createElement('script');
				js_script.type = "text/javascript";
				js_script.src = "//www.google.com/recaptcha/api.js?onload=pyloadCaptchaOnLoadCallback&render=explicit";
				js_script.async = true;
				document.getElementsByTagName('head')[0].appendChild(js_script);
			}"""

    RECAPTCHA_INVISIBLE_SIG = "6c6fb9970fdeac68b95809ce45a344f1225d2284e2c08507261f3506dbeebe9f0e1d9040df64191e" + \
                              "938f578b52009c31d0da920e1a9616d73ff7b7eb1e964477fac169e412fd1e325992c1783c4664e8" + \
                              "ba207986af12939fcc50bed642f8c26136cc8656a22be2fc51651437d1e0d356ae19a8c33d569f4d" + \
                              "7d11d3d794a074caf06f58bd2e2e339d31968967ad78c955ea36c707a8524ba3933509525a22e3ba" + \
                              "56ad3e71770700e6a1d18158db33f65f47d6558f16d2db5c75ab8b1be8595846a27f4aa514a98d7c" + \
                              "b13d6a557a1273ca5a06b1251f7481d787e3eca77523a8733be179318f46baaa1d99112daaf08c4f" + \
                              "86e067931f593c0f1941d9a8414fa1a4"

    RECAPTCHA_INVISIBLE_JS = """
			while(document.children[0].childElementCount > 0) {
				document.children[0].removeChild(document.children[0].children[0]);
			}
			document.children[0].innerHTML = '<html><head></head><body style="display:inline-block;"><div id="captchadiv" style="display: inline-block;"></div></body></html>';

			gpyload.data.sitekey = request.params.sitekey;
			// function that is called when the captcha finished loading and is ready to interact
			window.pyloadCaptchaOnLoadCallback = function() {
				grecaptcha.render (
					"captchadiv",
					{size: "invisible",
					 'sitekey': gpyload.data.sitekey,
					 'callback': function() {
						var recaptchaResponse = grecaptcha.getResponse(); // get captcha response
						gpyload.submitResponse(recaptchaResponse);
					 }}
				);
				grecaptcha.execute();
			};

			delete window.grecaptcha;
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
            key = urllib.parse.unquote(m.group(1).strip())
            m = re.search(self.KEY_FORMAT_V2_PATTERN, key)
            if m is not None:
                self.key = key
                self.log_debug(f"Key: {self.key}")
                return self.key

            else:
                self.log_debug(key, "Wrong key format, this probably because it is not a reCAPTCHA key")

        self.log_warning(self._("Key pattern not found"))
        return None

    def detect_secure_token(self, data=None):
        html = data or self.retrieve_data()

        m = re.search(self.STOKEN_V2_PATTERN, html)
        if m is not None:
            self.secure_token = m.group(1).strip()
            self.log_debug(f"Secure Token: {self.secure_token}")
            return self.secure_token
        else:
            self.log_warning(self._("Secure Token pattern not found"))
            return None

    def detect_version(self, data=None):
        data = data or self.retrieve_data()

        v2 = re.search(self.KEY_V2_PATTERN, data) is not None
        invisible = re.search(self.INVISIBLE_V2_PATTERN, data) is not None

        if v2 is True:
            if invisible is True:
                self.log_debug("Detected reCAPTCHA v2 invisible")
                return "2invisible"
            else:
                self.log_debug("Detected reCAPTCHA v2")
                return 2

        else:
            self.log_warning(
                self._("Could not properly detect reCAPTCHA version, defaulting to v2")
            )
            return 2

    def challenge(self, key=None, data=None, version=None, secure_token=None):
        key = key or self.retrieve_key(data)
        secure_token = (
            secure_token or self.detect_secure_token(data)
            if secure_token is not False
            else None
        )

        if version in (2, "2js", "2invisible"):
            return getattr(self, "_challenge_v{}".format(version))(
                key, secure_token=secure_token
            )
        else:
            return self.challenge(
                key,
                data,
                version=self.detect_version(data=data),
                secure_token=secure_token,
            )

    def _prepare_image(self, image, challenge_msg):
        dummy_text = "pk"
        # This is just a string to calculate biggest height of a text, since usually
        # the letters 'p' and 'k' reach to the lower most respective higher most
        # points in a text font (see typography) and thus we can hereby calculate
        # the biggest text height of a given font

        with io.StringIO() as s:
            s.write(image)
            s.seek(0)

            img = Image.open(s)
            draw = ImageDraw.Draw(img)

            font_name = "arialbd"

            if os.name == "nt":
                font = ImageFont.truetype(font_name, 13)
            else:
                font = None

            tile_size = {"width": img.size[0] // 3, "height": img.size[1] // 3}
            tile_index_size = {
                "width": draw.textsize("0")[0],
                "height": draw.textsize("0")[1],
            }

            margin = 2
            for x in range(3):
                for y in range(3):
                    tile_index_pos = {
                        "x": x * tile_size["width"]
                        + (tile_size["width"] // 2)
                        - (tile_index_size["width"] // 2),
                        "y": y * tile_size["height"],
                    }

                    draw.rectangle(
                        [
                            tile_index_pos["x"] - margin,
                            tile_index_pos["y"],
                            tile_index_pos["x"] + tile_index_size["width"] + margin,
                            tile_index_pos["y"] + tile_index_size["height"],
                        ],
                        fill="white",
                    )

                    index_number = str(y * 3 + x + 1)
                    text_width, text_height = draw.textsize(index_number, font=font)

                    draw.text(
                        (
                            tile_index_pos["x"]
                            + (tile_index_size["width"] // 2)
                            - (text_width // 2),
                            tile_index_pos["y"]
                            + (tile_index_size["height"] // 2)
                            - (text_height // 2),
                        ),
                        index_number,
                        "#000",
                        font=font,
                    )

            if os.name == "nt":
                font = ImageFont.truetype(font_name, 16)

            _sol = 0
            _eol = 1
            while True:
                # determine maximum width of line
                while draw.textsize(challenge_msg[_sol:_eol], font=font)[0] < img.size[
                    0
                ] and _eol < len(challenge_msg):
                    _eol += 1

                # if we've wrapped the text, then adjust the wrap to the last word
                if _eol < len(challenge_msg):
                    _eol = challenge_msg.rfind(" ", 0, _eol)
                    if _eol > 0:
                        challenge_msg = (
                            challenge_msg[:_eol] + "\n" + challenge_msg[_eol + 1:]
                        )
                        _sol = _eol + 1
                else:
                    break

            message = challenge_msg + '\n(Type image numbers like "258")'

            # the text's real height is twice as big as returned by font.getsize() since we use
            # a newline character which indeed breaks the text but doesn't count as a second line
            # in font.getsize().
            if os.name == "nt":
                text_area_height = draw.multiline_textsize(message, font=font)[1]

            else:
                lines = message.split("\n")
                text_area_height = len(lines) * draw.textsize(dummy_text, font=font)[1]

            margin = 5
            text_area_height = (
                text_area_height + margin * 2
            )  #: add some margin on top and bottom of text

            img2 = Image.new(
                "RGB", (img.size[0], img.size[1] + text_area_height), "white"
            )
            img2.paste(img, (0, text_area_height))
            draw = ImageDraw.Draw(img2)

            if os.name == "nt":
                draw.text((3, margin), message, fill="black", font=font)
            else:
                for i in range(len(lines)):
                    draw.text(
                        (3, i * draw.textsize(dummy_text, font=font)[1] + margin),
                        lines[i],
                        fill="black",
                        font=font,
                    )

            s.truncate(0)
            img2.save(s, format="JPEG")
            img = s.getvalue()

        return img

    def _challenge_v2(self, key, secure_token=None):
        fallback_url = (
            "http://www.google.com/recaptcha/api/fallback?k="
            + key
            + ("&stoken=" + secure_token if secure_token else "")
        )

        html = self.pyfile.plugin.load(fallback_url, ref=self.pyfile.url)

        if (
            re.search(r'href="https://support.google.com/recaptcha.*"', html)
            is not None
        ):
            self.log_warning(
                self._("reCAPTCHA noscript is blocked, trying reCAPTCHA interactive")
            )
            return self._challenge_v2js(key, secure_token=secure_token)

        for i in range(10):
            try:
                challenge = re.search(r'name="c"\s+value=\s*"([^"]+)', html).group(1)

            except (AttributeError, IndexError):
                self.fail(self._("reCAPTCHA challenge pattern not found"))

            try:
                challenge_msg = re.search(
                    r'<label .*?class="fbc-imageselect-message-text">(.*?)</label>',
                    html,
                ).group(1)

            except (AttributeError, IndexError):
                try:
                    challenge_msg = re.search(
                        r"<div .*?class=\"fbc-imageselect-message-error\">(.*?)</div>",
                        html,
                    ).group(1)

                except (AttributeError, IndexError):
                    self.fail(self._("reCAPTCHA challenge message not found"))

            challenge_msg = re.sub(r"<.*?>", "", challenge_msg)

            image_url = urllib.parse.urljoin(
                "http://www.google.com",
                re.search(r'"(/recaptcha/api2/payload[^"]+)', html).group(1),
            )

            img = self.pyfile.plugin.load(image_url, ref=fallback_url, decode=False)

            img = self._prepare_image(img, challenge_msg)

            response = self.decrypt_image(img)

            post_str = (
                "c="
                + urllib.parse.quote_plus(challenge)
                + "".join(
                    "&response={}".format(str(int(k) - 1))
                    for k in response
                    if k.isdigit()
                )
            )
            html = self.pyfile.plugin.load(
                fallback_url, post=post_str, ref=fallback_url
            )

            try:
                result = re.search(
                    r'<div class="fbc-verification-token"><textarea .*readonly>(.*?)</textarea>',
                    html,
                ).group(1)
                self.correct()
                break

            except (AttributeError, IndexError):
                self.invalid()

        else:
            self.fail(self._("reCAPTCHA max retries exceeded"))

        return result

    # solve interactive captcha (javascript required), use when non-JS captcha
    # fallback for v2 is not allowed
    def _challenge_v2js(self, key, secure_token=None):
        self.log_debug("Challenge reCAPTCHA v2 interactive")

        params = {
            "url": self.pyfile.url,
            "sitekey": key,
            "securetoken": secure_token,
            "script": {
                "signature": self.RECAPTCHA_INTERACTIVE_SIG,
                "code": self.RECAPTCHA_INTERACTIVE_JS,
            },
        }

        result = self.decrypt_interactive(params, timeout=300)

        return result

    # solve invisible captcha (browser only, no user interaction)
    def _challenge_v2invisible(self, key, secure_token=None):
        self.log_debug("Challenge reCAPTCHA v2 invisible")

        params = {
            "url": self.pyfile.url,
            "sitekey": key,
            "securetoken": secure_token,
            "script": {
                "signature": self.RECAPTCHA_INVISIBLE_SIG,
                "code": self.RECAPTCHA_INVISIBLE_JS,
            },
        }

        result = self.decrypt_invisible(params, timeout=300)

        return result


if __name__ == "__main__":
    # Sign with the command:
    # `python -m pyload.plugins.anticaptchas.ReCaptcha RECAPTCHA_INTERACTIVE_JS pyload.private.pem pem_passphrase`
    import sys
    from ..helpers import sign_string

    if len(sys.argv) > 3:
        with open(sys.argv[2]) as fp:
            pem_private = fp.read()

        print(
            sign_string(
                getattr(ReCaptcha, sys.argv[1]),
                pem_private,
                pem_passphrase=sys.argv[3],
                sign_algo="SHA384",
            )
        )
