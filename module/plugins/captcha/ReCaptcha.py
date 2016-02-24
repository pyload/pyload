# -*- coding: utf-8 -*-

from StringIO import StringIO
import os
import re
import urlparse

from bs4 import BeautifulSoup as Soup
import requests

from module.plugins.internal.CaptchaService import CaptchaService

try:
    from PIL import Image
    from PIL import ImageDraw
    from PIL import ImageFont
except ImportError:
    import Image
    import ImageDraw
    import ImageFont


class ReCaptcha(CaptchaService):
    __name__ = 'ReCaptcha'
    __type__ = 'captcha'
    __version__ = '0.22'
    __status__ = 'testing'
    __description__ = 'ReCaptcha captcha service plugin'
    __license__ = 'GPLv3'
    __authors__ = [
        ('pyLoad Team', 'admin@pyload.org'),
        ('Walter Purcaro', 'vuolter@gmail.com'),
        ('zapp-brannigan', 'fuerst.reinje@web.de'),
        ('Arno-Nymous', None)
    ]


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

        except AttributeError:
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

        except AttributeError:
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


    def prepare_image(self, image):
        # This is just a string to calculate biggest height of a text, since usually
        # the letters 'p' and 'k' reach to the lower most respective higher most
        # points in a text font (see typography) and thus we can hereby calculate
        # the biggest text height of a given font
        dummyText = 'pk'

        fontName = 'arialbd'
        s = StringIO()
        s.write(image)
        s.seek(0)
        
        img = Image.open(s)
        draw = ImageDraw.Draw(img)
        if os.name == 'nt':
            font = ImageFont.truetype(fontName, 13)
        else:
            font = None

        tileSize = {'width': img.size[0] / 3, 'height': img.size[1] / 3}
        tileIndexSize = {'width': draw.textsize('0')[0], 'height': draw.textsize('0')[1]}

        for i in range(3):
            for j in range(3):
                tileIndexPos = {
                    'x': i * tileSize['width'] + (tileSize['width'] / 2) - (tileIndexSize['width'] / 2),
                    'y': j * tileSize['height']
                }
                draw.rectangle(
                    [
                        tileIndexPos['x'],
                        tileIndexPos['y'],
                        tileIndexPos['x'] + tileIndexSize['width'],
                        tileIndexPos['y'] + tileIndexSize['height']
                    ],
                    fill='white'
                )
                indexNumber = str(j * 3 + i + 1)
                textWidth, textHeight = draw.textsize(indexNumber, font=font)
                draw.text(
                    (
                        tileIndexPos['x'] + (tileIndexSize['width'] / 2) - (textWidth / 2),
                        tileIndexPos['y'] + (tileIndexSize['height'] / 2) - (textHeight / 2)
                    ),
                    indexNumber,
                    '#000',
                    font=font
                )

        if os.name == 'nt':
            font = ImageFont.truetype(fontName, 16)
        message = self.v2ChallengeMsg + '\n(Type image numbers like "258")'
        # the text's real height is twice as big as returned by font.getsize() since we use
        # a newline character which indeed breaks the text but doesn't count as a second line
        # in font.getsize().
        if os.name == 'nt':
            textHeight = draw.multiline_textsize(message, font=font)[1]
        else:
            lines = message.split('\n')
            textHeight = len(lines) * draw.textsize(dummyText, font=font)[1]
        margin = 5
        textHeight = textHeight + margin * 2  #  add some margin on top and bottom of text
        img2 = Image.new('RGB', (img.size[0], img.size[1] + textHeight), 'white')
        img2.paste(img, (0, textHeight))
        draw = ImageDraw.Draw(img2)
        if os.name == 'nt':
            draw.text((3, margin), message, fill='black', font=font)
        else:
            for i in range(len(lines)):
                draw.text((3, i * draw.textsize(dummyText)[1] + margin), lines[i], fill='black', font=font)
        s.truncate(0)
        img2.save(s, format='JPEG')
        img = s.getvalue()
        s.close()
        return img


    def _challenge_v2(self, key, parent=None):
        fallbackURL = 'http://www.google.com/recaptcha/api/fallback?k=' + key
        session = requests.Session()

        fallback = session.get(
            fallbackURL,
            headers={
                'Referer': self.pyfile.url
            }
        )
        fallback = Soup(fallback.text, 'html5lib')

        while True:
            c = fallback.find('input', {'name': 'c', 'type': 'hidden'})['value']

            try:
                challengeMessage = fallback.find('label', {'class': 'fbc-imageselect-message-text'}).text
            except:
                challengeMessage = fallback.find('div', {'class': 'fbc-imageselect-message-error'}).text
            self.v2ChallengeMsg = challengeMessage

            imageURL = 'http://www.google.com' + fallback.find('img', {'class': 'fbc-imageselect-payload'})['src']
            img = self.load(
                imageURL,
                req=self.pyfile.plugin.req,
                get={},
                post={},
                ref=False,
                cookies=True,
                decode=False
            )
            img = self.prepare_image(img)
            response = self.decrypt_image(img)

            a = {'c': c}
            b = {'response': [int(k) - 1 for k in response if k.isdigit()]}
            d = dict(a, **b)
            fallback = session.post(
                fallbackURL,
                headers={'Referer': fallbackURL},
                data=d
            )

            fallback = Soup(fallback.text, 'html5lib')

            recaptchaTokenTextarea = fallback.find('div', {'class': 'fbc-verification-token'})
            if recaptchaTokenTextarea:
                recaptchaVerificationToken = recaptchaTokenTextarea.textarea.text
                break

        return recaptchaVerificationToken
