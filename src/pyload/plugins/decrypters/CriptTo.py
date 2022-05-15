# -*- coding: utf-8 -*-

import base64
import re
import json

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from pyload.core.utils.convert import to_str

from ..anticaptchas.ReCaptcha import ReCaptcha
from ..anticaptchas.SolveMedia import SolveMedia
from ..containers.DLC import BadDLC, DLCDecrypter
from ..helpers import parse_html_form
from ..base.simple_decrypter import SimpleDecrypter


class CriptTo(SimpleDecrypter):
    __name__ = "CriptTo"
    __type__ = "decrypter"
    __version__ = "0.05"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?cript\.to/folder/(?P<ID>\w+)'
    __config__ = [("enabled", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("folder_per_package", "Default;Yes;No", "Create folder for each package", "Default"),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Cript.to decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    URL_REPLACEMENTS = [(__pattern__ + ".*", "https://cript.to/folder/\g<ID>")]

    CNL_LINK_PATTERN = r'data-cnl="(.+?)"'
    WEB_LINK_PATTERN = r'href="javascript:void\(0\);" onclick="popup\(\'(.+?)\''
    DLC_LINK_PATTERN = r'onclick="popup\(\'(https://cript\.to/dlc/.+?)\''

    def api_info(self, url):
        info = {}

        folder_id = re.match(self.__pattern__, url).group('ID')
        folder_info = json.loads(self.load("https://cript.to/api/v1/folder/info",
                                         get={'id': folder_id}))
        if folder_info["status"] == "error":
            info["status"] = 8
            info["error"] = folder_info["message"]

        else:
            info["status"] = 2
            info["name"] = folder_info["data"]["name"]

        return info

    def decrypt(self, pyfile):
        self.data = self.load(pyfile.url)

        self.handle_captcha()

        self.handle_password()

        for handle in (self.handle_CNL,
                       self.handle_weblinks,
                       self.handle_DLC):
            urls = handle()
            if urls:
                self.packages = [(self.pyfile.name or pyfile.package().name,
                                  urls,
                                  self.pyfile.name or pyfile.package().name)]
                return

            elif self.packages:
                return

    def handle_captcha(self):
        url, inputs = self.parse_html_form('action="{}"'.format(self.pyfile.url))
        if inputs is None:
            return

        elif inputs["do"] == "captcha":
            captcha_type = inputs["captcha_driver"]

            if captcha_type == "simplecaptcha":
                self.log_debug("Internal captcha found")

                captcha_url = "https://cript.to/captcha/simplecaptcha"
                captcha_code = self.captcha.decrypt(captcha_url, input_type="png")
                inputs["simplecaptcha"] = captcha_code

            elif captcha_type == "circlecaptcha":
                self.log_debug("Circle captcha found")

                captcha_url = "https://cript.to/captcha/circlecaptcha"
                captcha_code = self.captcha.decrypt(captcha_url, input_type="png", output_type="positional")
                inputs["button.x"] = captcha_code[0]
                inputs["button.y"] = captcha_code[1]

            elif captcha_type == "solvemedia":
                solvemedia = SolveMedia(self.pyfile)
                captcha_key = solvemedia.detect_key()

                if captcha_key:
                    self.log_debug("Solvemedia captcha found")

                    self.captcha = solvemedia
                    response, challenge = solvemedia.challenge(captcha_key)

                    inputs["adcopy_challenge"] = challenge
                    inputs["adcopy_response"] = response

                else:
                    self.log_warning(self._("Could not detect Solvemedia captcha key"))
                    self.retry_captcha()

            elif captcha_type == "recaptcha":
                recaptcha = ReCaptcha(self.pyfile)
                captcha_key = recaptcha.detect_key()

                if captcha_key:
                    self.log_debug("ReCaptcha captcha found")

                    self.captcha = recaptcha
                    response = recaptcha.challenge(captcha_key)

                    inputs["g-recaptcha-response"] = response

                else:
                    self.log_warning(self._("Could not detect ReCaptcha captcha key"))
                    self.retry_captcha()

            else:
                self.log_warning(self._("Captcha Not found"))

            inputs["submit"] = "confirm"

            self.data = self.load(url, post=inputs)
            url, inputs = self.parse_html_form('action="{}"'.format(self.pyfile.url))
            if inputs is not None:
                if inputs["do"] == "captcha":
                    self.captcha.invalid()
                    self.retry_captcha()

    def handle_password(self):
        url, inputs = self.parse_html_form('action="{}"'.format(self.pyfile.url))
        if inputs is None:
            return

        elif inputs["do"] == "password":
            password = self.get_password()
            if not password:
                self.fail(self._("Password required"))

            inputs["password"] = password
            inputs["submit"] = "confirm"

            self.data = self.load(url, post=inputs)

            if "That Password was incorrect" in self.data:
                self.fail(self._("Wrong password"))

    def handle_CNL(self):
        links = []

        m = re.search(self.CNL_LINK_PATTERN, self.data)
        if m is not None:
            html = self.load(m.group(1))
            _, inputs = parse_html_form("/flash/", html)
            if inputs is not None:
                #: Get key
                key = bytes.fromhex(re.search(r"'(\w+)'", inputs['jk']).group(1))
                crypted = inputs["crypted"]

                #: Decrypt
                #Key = key
                #IV = key
                cipher = Cipher(
                    algorithms.AES(key), modes.CBC(key), backend=default_backend()
                )
                decryptor = cipher.decryptor()
                text = decryptor.update(base64.b64decode(crypted)) + decryptor.finalize()

                #: Extract links
                text = to_str(text).replace("\x00", "")
                links = [item for item in text.splitlines() if item]

        return links

    def handle_weblinks(self):
        links = []

        weblinks = re.findall(self.WEB_LINK_PATTERN, self.data)
        for weblink in weblinks:
            html = self.load(weblink)
            link = self.last_header["url"]
            if link == "https://cript.to/bot":
                for _i in range(3):
                    url, inputs = parse_html_form("/bot", html)
                    if inputs is None or "circlecaptcha" not in html:
                        continue

                    captcha_url = "https://cript.to/captcha/circlecaptcha"
                    captcha_code = self.captcha.decrypt(captcha_url, input_type="png", output_type="positional")
                    inputs["button.x"] = captcha_code[0]
                    inputs["button.y"] = captcha_code[1]
                    html = self.load(url, post=inputs)
                    link = self.last_header["url"]
                    if not link.startswith("https://cript.to"):
                        self.captcha.correct()
                        break

                    else:
                        self.captcha.invalid()

                else:
                        self.log_warning(self._("Could not parse weblink (bot)"))
                        links = []
                        break

            if link:
                links.append(link)

        return links

    def handle_DLC(self):
        decrypter = DLCDecrypter(self)

        dlc_urls = re.findall(self.DLC_LINK_PATTERN, self.data)
        for dlc_url in dlc_urls:
            dlc_data = self.load(dlc_url)
            try:
                packages = decrypter.decrypt(dlc_data)

            except BadDLC:
                self.log_warning(self._("Container is corrupted"))
                continue

            self.packages.extend([(name or self.pyfile.name, links, name or self.pyfile.name)
                                  for name, links in packages])

        return []
