# -*- coding: utf-8 -*-

import os
import re
import urllib
import urlparse

from StringIO import StringIO
from module.plugins.internal.CaptchaService import CaptchaService

try:
    no_pil = False
    from PIL import _imaging
    from PIL import Image
    from PIL import ImageDraw
    from PIL import ImageFont

except ImportError:
    try:
        import _imaging
        import Image
        import ImageDraw
        import ImageFont

    except ImportError:
        no_pil = True


class ReCaptcha(CaptchaService):
    __name__    = 'ReCaptcha'
    __type__    = 'captcha'
    __version__ = '0.27'
    __status__  = 'testing'

    __description__ = 'ReCaptcha captcha service plugin'
    __license__     = 'GPLv3'
    __authors__     = [('Walter Purcaro', 'vuolter@gmail.com'   ),
                       ('zapp-brannigan', 'fuerst.reinje@web.de'),
                       ('Arno-Nymous'   , None                  )]


    KEY_V1_PATTERN = r'(?:recaptcha(?:/api|\.net)/(?:challenge|noscript)\?k=|Recaptcha\.create\s*\(\s*["\'])([\w\-]+)'
    KEY_V2_PATTERN = r'(?:data-sitekey=["\']|["\']sitekey["\']:\s*["\'])([\w\-]+)'


    def detect_key(self, data=None):
        html = data or self.retrieve_data()

        m = re.search(self.KEY_V2_PATTERN, html) or re.search(self.KEY_V1_PATTERN, html)
        if m is not None:
            self.key = m.group(1).strip()
            self.log_debug("Key: %s" % self.key)
            return self.key
        else:
            self.log_warning(_("Key pattern not found"))
            return None


    def challenge(self, key=None, data=None, version=None):
        key = key or self.retrieve_key(data)

        if version in (1, 2):
            return getattr(self, "_challenge_v%s" % version)(key)

        else:
            return self.challenge(key,
                                  version=2 if re.search(self.KEY_V2_PATTERN, data or self.retrieve_data()) else 1)


    def _challenge_v1(self, key):
        html = self.pyfile.plugin.load("http://www.google.com/recaptcha/api/challenge",
                                    get={'k': key})
        try:
            challenge = re.search("challenge : '(.+?)',", html).group(1)
            server    = re.search("server : '(.+?)',", html).group(1)

        except (AttributeError, IndexError):
            self.fail(_("ReCaptcha challenge pattern not found"))

        self.log_debug("Challenge: %s" % challenge)

        return self.result(server, challenge, key)


    def result(self, server, challenge, key):
        self.pyfile.plugin.load("http://www.google.com/recaptcha/api/js/recaptcha.js")
        html = self.pyfile.plugin.load("http://www.google.com/recaptcha/api/reload",
                                    get={'c'     : challenge,
                                         'k'     : key,
                                         'reason': "i",
                                         'type'  : "image"})

        try:
            challenge = re.search('\(\'(.+?)\',',html).group(1)

        except (AttributeError, IndexError):
            self.fail(_("ReCaptcha second challenge pattern not found"))

        self.log_debug("Second challenge: %s" % challenge)
        result = self.decrypt(urlparse.urljoin(server, "image"),
                              get={'c': challenge},
                              cookies=True,
                              input_type="jpg")

        return result, challenge


    def _collect_api_info(self):
        html = self.pyfile.plugin.load("http://www.google.com/recaptcha/api.js")
        a    = re.search(r'po.src = \'(.*?)\';', html).group(1)
        vers = a.split("/")[5]

        self.log_debug("API version: %s" % vers)

        language = a.split("__")[1].split(".")[0]

        self.log_debug("API language: %s" % language)

        html = self.pyfile.plugin.load("https://apis.google.com/js/api.js")
        b    = re.search(r'"h":"(.*?)","', html).group(1)
        jsh  = b.decode('unicode-escape')

        self.log_debug("API jsh-string: %s" % jsh)

        return vers, language, jsh


    def _prepare_image(self, image, challenge_msg):
        if no_pil:
            self.log_error(_("Missing PIL lib"), _("Please install python's PIL library"))
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

        tile_size       = {'width': img.size[0] / 3, 'height': img.size[1] / 3}
        tile_index_size = {'width': draw.textsize('0')[0], 'height': draw.textsize('0')[1]}

        margin = 2
        for x in xrange(3):
            for y in xrange(3):
                tile_index_pos = {
                    'x': x * tile_size['width'] + (tile_size['width'] / 2) - (tile_index_size['width'] / 2),
                    'y': y * tile_size['height']
                }

                draw.rectangle(
                    [
                        tile_index_pos['x'] - margin,
                        tile_index_pos['y'],
                        tile_index_pos['x'] + tile_index_size['width'] + margin,
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
            while draw.textsize(challenge_msg[_sol:_eol], font=font)[0] < img.size[0] and _eol < len(challenge_msg):
                _eol += 1

            # if we've wrapped the text, then adjust the wrap to the last word
            if _eol < len(challenge_msg):
                _eol = challenge_msg.rfind(" ", 0, _eol)
                if _eol > 0:
                    challenge_msg = challenge_msg[:_eol] + '\n' + challenge_msg[_eol+1:]
                    _sol = _eol+1
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
        text_area_height = text_area_height + margin * 2  #  add some margin on top and bottom of text

        img2 = Image.new('RGB', (img.size[0], img.size[1] + text_area_height), 'white')
        img2.paste(img, (0, text_area_height))
        draw = ImageDraw.Draw(img2)

        if os.name == 'nt':
            draw.text((3, margin), message, fill='black', font=font)
        else:
            for i in xrange(len(lines)):
                draw.text((3, i * draw.textsize(dummy_text, font=font)[1] + margin), lines[i], fill='black', font=font)

        s.truncate(0)
        img2.save(s, format='JPEG')
        img = s.getvalue()
        s.close()

        return img


    def _challenge_v2(self, key):
        fallback_url = 'http://www.google.com/recaptcha/api/fallback?k=' + key

        html = self.pyfile.plugin.load(fallback_url, ref=self.pyfile.url)

        for i in xrange(10):
            try:
                challenge = re.search(r'name="c"\s+value=\s*"([^"]+)', html).group(1)

            except (AttributeError, IndexError):
                self.fail(_("ReCaptcha challenge pattern not found"))

            try:
                challenge_msg = re.search(r'<label .*?class="fbc-imageselect-message-text">(.*?)</label>', html).group(1)

            except (AttributeError, IndexError):
                try:
                    challenge_msg = re.search(r'<div .*?class=\"fbc-imageselect-message-error\">(.*?)</div>', html).group(1)

                except (AttributeError, IndexError):
                    self.fail(_("ReCaptcha challenge message not found"))

            challenge_msg = re.sub(r'</?\w+?>', "", challenge_msg)

            image_url = urlparse.urljoin('http://www.google.com',
                                         re.search(r'"(/recaptcha/api2/payload[^"]+)', html).group(1))

            img = self.pyfile.plugin.load(image_url, ref=fallback_url, decode=False)

            img = self._prepare_image(img, challenge_msg)

            response = self.decrypt_image(img)

            post_str = "c=" + urllib.quote_plus(challenge) +\
                       "".join("&response=%s" % str(int(k) - 1) for k in response if k.isdigit())
            html = self.pyfile.plugin.load(fallback_url, post=post_str, ref=fallback_url)

            try:
                result = re.search(r'"this\.select\(\)">(.*?)</textarea>', html).group(1)
                break

            except (AttributeError, IndexError):
                pass

        else:
            self.fail(_("Recaptcha max retries exceeded"))

        return result, challenge
