# -*- coding: utf-8 -*-

import base64
import re

from cryptography.fernet import Fernet

import pycurl
from pyload.core.utils.misc import eval_js
from pyload.core.utils.old import html_unescape

from ..base.decrypter import BaseDecrypter
from ..helpers import set_cookie


class LinkCryptWs(BaseDecrypter):
    __name__ = "LinkCryptWs"
    __type__ = "decrypter"
    __version__ = "0.21"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?linkcrypt\.ws/(dir|container)/(?P<ID>\w+)"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """LinkCrypt.ws decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("kagenoshin", "kagenoshin[AT]gmx[DOT]ch"),
        ("glukgluk", None),
        ("Gummibaer", None),
        ("Arno-Nymous", None),
    ]

    CRYPTED_KEY = "crypted"
    JK_KEY = "jk"

    def setup(self):
        self.urls = []
        self.sources = ["cnl", "web", "dlc", "rsdf", "ccf"]

    def prepare(self):
        #: Init
        self.fileid = re.match(self.__pattern__, self.pyfile.url).group("ID")

        set_cookie(self.req.cj, "linkcrypt.ws", "language", "en")

        #: Request package
        #: Better chance to not get those key-captchas
        self.req.http.c.setopt(
            pycurl.USERAGENT,
            "Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; rv:11.0) like Gecko",
        )
        self.data = self.load(self.pyfile.url)
        self.data = self.load(self.pyfile.url)

    def decrypt(self, pyfile):
        self.prepare()

        if not self.is_online():
            self.offline()

        if self.is_key_captcha_protected():
            self.retry(8, 15, self._("Can't handle Key-Captcha"))

        if self.is_captcha_protected():
            self.unlock_captcha_protection()
            self.handle_captcha_errors()

        #: Check for protection
        if self.is_password_protected():
            self.unlock_password_protection()
            self.handle_errors()

        #: Get unrar password
        self.getunrarpw()

        #: Get package name and folder
        pack_name, folder_name = self.get_package_info()

        #: Get the container definitions from script section
        self.get_container_html()

        #: Extract package links
        for source_type in self.sources:
            links = self.handle_link_source(source_type)

            if links:
                self.urls.extend(links)
                break

        if self.urls:
            self.packages = [(pack_name, self.urls, folder_name)]

    def is_online(self):
        if "<title>Linkcrypt.ws // Error 404</title>" in self.data:
            self.log_debug("Folder doesn't exist anymore")
            return False
        else:
            return True

    def is_password_protected(self):
        if "Authorizing" in self.data:
            self.log_debug("Links are password protected")
            return True
        else:
            return False

    def is_captcha_protected(self):
        if ("Linkcrypt.ws // Captx" in self.data) or (
            "Linkcrypt.ws // TextX" in self.data
        ):
            self.log_debug("Links are captcha protected")
            return True
        else:
            return False

    def is_key_captcha_protected(self):
        if re.search(r">If the folder does not open after klick on <", self.data, re.I):
            return True
        else:
            return False

    def unlock_password_protection(self):
        password = self.get_password()

        if password:
            self.log_debug(
                "Submitting password [{}] for protected links".format(password)
            )
            self.data = self.load(
                self.pyfile.url, post={"password": password, "x": "0", "y": "0"}
            )
        else:
            self.fail(self._("Folder is password protected"))

    def unlock_captcha_protection(self):
        captcha_url = "http://linkcrypt.ws/captx.html?secid=id=&id="
        captcha_code = self.captcha.decrypt(
            captcha_url, input_type="gif", output_type="positional"
        )

        self.data = self.load(
            self.pyfile.url, post={"x": captcha_code[0], "y": captcha_code[1]}
        )

    def get_package_info(self):
        name = self.pyfile.package().name
        folder = self.pyfile.package().folder

        self.log_debug(
            "Defaulting to pyfile name [{}] and folder [{}] for package".format(
                name, folder
            )
        )

        return name, folder

    def getunrarpw(self):
        # Skip password parsing, since the method was not reliable due to the scrambling of the form data.
        # That way one could not predict the exact position of the password at
        # a certain index.
        return

    def handle_errors(self):
        if self.is_password_protected():
            self.fail(self._("Wrong password"))

    def handle_captcha_errors(self):
        if "Your choice was wrong" in self.data:
            self.retry_captcha()
        else:
            self.captcha.correct()

    def handle_link_source(self, source_type):
        if source_type == "cnl":
            return self.handle_CNL2()

        elif source_type == "web":
            return self.handle_web_links()

        elif source_type in ("rsdf", "ccf", "dlc"):
            return self.handle_container(source_type)

        else:
            # TODO: Replace with self.error in 0.6.x
            self.fail(self._("Unknown source type: {}").format(source_type))

    def handle_web_links(self):
        self.log_debug("Search for Web links ")

        pack_links = []
        pattern = r'<form action="http://linkcrypt.ws/out.html"[^>]*?>.*?<input[^>]*?value="(.+?)"[^>]*?name="file"'
        ids = re.findall(pattern, self.data, re.I | re.S)

        self.log_debug(f"Decrypting {len(ids)} Web links")

        for idx, weblink_id in enumerate(ids):
            try:
                res = self.load(
                    "http://linkcrypt.ws/out.html", post={"file": weblink_id}
                )

                indexs = res.find("href=doNotTrack('") + 17
                indexe = res.find("'", indexs)

                link2 = res[indexs:indexe]

                link2 = html_unescape(link2)
                pack_links.append(link2)

            except Exception as detail:
                self.log_debug(
                    "Error decrypting Web link {}, {}".format(weblink_id, detail)
                )

        return pack_links

    def get_container_html(self):
        self.container_html = []

        script = re.search(
            r'<script.*?javascript[^>]*?>.*(eval.*?)\s*eval.*</script>.*<div class="clearfix',
            self.data,
            re.I | re.S,
        )

        if script:
            container_html_text = script.group(1)
            container_html_text.strip()
            self.container_html = container_html_text.splitlines()

    def handle_javascript(self, line):
        return eval_js(
            line.replace(
                "{}))",
                "{}).replace('document.open();document.write','').replace(';document.close();',''))",
            )
        )

    def handle_container(self, container_type):
        pack_links = []
        container_type = container_type.lower()

        self.log_debug(f"Search for {container_type.upper()} Container links")

        if (
            not container_type.isalnum()
        ):  #: Check to prevent broken re-pattern (cnl2, rsdf, ccf, dlc, web are all alpha-numeric)
            # TODO: Replace with self.error in 0.6.x
            self.fail(self._("Unknown container type: {}").format(container_type))

        for line in self.container_html:
            if container_type in line:
                jseval = self.handle_javascript(line)
                clink = re.search(r'href=["\'](["\']+)', jseval, re.I)

                if not clink:
                    continue

                self.log_debug("clink found")

                pack_name, folder_name = self.get_package_info()
                self.log_debug(
                    "Added package with name {}.{} and container link {}".format(
                        pack_name, container_type, clink.group(1)
                    )
                )
                self.pyload.api.uploadContainer(
                    ".".join([pack_name, container_type]), self.load(clink.group(1))
                )
                return "Found it"

        return pack_links

    def handle_CNL2(self):
        self.log_debug("Search for CNL links")

        pack_links = []
        cnl_line = None

        for line in self.container_html:
            if "addcrypted2" in line:
                cnl_line = line
                break

        if cnl_line:
            self.log_debug("cnl_line found")

        try:
            cnl_section = self.handle_javascript(cnl_line)
            (vcrypted, vjk) = self._get_cipher_params(cnl_section)
            for (crypted, jk) in zip(vcrypted, vjk):
                pack_links.extend(self._get_links(crypted, jk))

        except Exception:
            self.log_error(
                self._("Unable to decrypt CNL links (JS Error) try to get over links"),
                exc_info=self.pyload.debug > 1,
                stack_info=self.pyload.debug > 2,
            )
            return self.handle_web_links()

        return pack_links

    def _get_cipher_params(self, cnl_section):
        #: Get jk
        jk_re = r'<INPUT.*?NAME="{}".*?VALUE="\D*(\d*)\D*"'.format(LinkCryptWs.JK_KEY)
        vjk = re.findall(jk_re, cnl_section)

        #: Get crypted
        crypted_re = r'<INPUT.*?NAME="{}".*?VALUE="(.*?)"'.format(
            LinkCryptWs.CRYPTED_KEY
        )
        vcrypted = re.findall(crypted_re, cnl_section)

        #: Log and return
        self.log_debug(f"Detected {len(vcrypted)} crypted blocks")
        return vcrypted, vjk

    def _get_links(self, crypted, jk):
        #: Get key
        key = bytes.fromhex(jk)

        self.log_debug(f"JsEngine returns value [{key}]")

        #: Decrypt
        obj = Fernet(key)
        text = obj.decrypt(base64.b64decode(crypted))

        #: Extract links
        text = text.replace("\x00", "").replace("\r", "")
        links = [link for link in text.split("\n") if link]

        #: Log and return
        self.log_debug(f"Package has {len(links)} links")

        return links
