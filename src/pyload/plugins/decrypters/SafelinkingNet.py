# -*- coding: utf-8 -*-
import json

import pycurl
from pyload.core.network.http.exceptions import BadHeader

from ..anticaptchas.SolveMedia import SolveMedia
from ..base.decrypter import BaseDecrypter


class SafelinkingNet(BaseDecrypter):
    __name__ = "SafelinkingNet"
    __type__ = "decrypter"
    __version__ = "0.22"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?safelinking\.net/(?P<TYPE>[pd]/)?(?P<ID>\w{7})"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        (
            "folder_per_package",
            "Default;Yes;No",
            "Create folder for each package",
            "Default",
        ),
    ]

    __description__ = """Safelinking.net decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("quareevo", "quareevo@arcor.de"),
        ("tbsn", "tbsnpy_github@gmx.de"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    # Safelinking seems to use a static SolveMedia key
    SOLVEMEDIA_KEY = "OZ987i6xTzNs9lw5.MA-2Vxbc-UxFrLu"

    def api_request(self, url, post_data):
        self.req.http.c.setopt(
            pycurl.HTTPHEADER,
            [
                "Accept: application/json, text/plain, */*",
                "Content-Type: application/json",
            ],
        )

        try:
            res = json.loads(self.load(url, post=json.dumps(post_data)))

        except (BadHeader, ValueError) as exc:
            self.log_error(exc)
            self.fail(exc)

        # Headers back to normal
        self.req.http.c.setopt(
            pycurl.HTTPHEADER,
            [
                "Accept: */*",
                "Accept-Language: en-US,en",
                "Accept-Charset: ISO-8859-1,utf-8;q=0.7,*;q=0.7",
                "Connection: keep-alive",
                "Keep-Alive: 300",
                "Expect:",
            ],
        )

        return res

    def decrypt(self, pyfile):
        # Process direct links
        if self.info["pattern"]["TYPE"] == "d/":
            header = self.load(pyfile.url, just_header=True)

            if "location" in header:
                self.links = [header.get("location")]

            else:
                self.error(self._("Couldn't find forwarded Link"))

        else:  #: Process protected links
            self.package_password = self.get_password()

            post_data = {"hash": self.info["pattern"]["ID"]}

            link_info = self.api_request(
                "http://safelinking.net/v1/protected", post_data
            )

            if "messsage" in link_info:
                self.log_error(link_info["messsage"])
                self.fail(link_info["messsage"])

            # Response: Links
            elif "links" in link_info:
                for link in link_info["links"]:
                    self.links.append(link["url"])
                    return

            if link_info["security"].get("usePassword", False):
                if self.package_password:
                    self.log_debug("Using package password")
                    post_data["password"] = self.package_password

                else:
                    self.fail(self._("Password required"))

            if link_info["security"].get("useCaptcha", False):
                self.captcha = SolveMedia(pyfile)
                response, challenge = self.captcha.challenge(self.SOLVEMEDIA_KEY)

                post_data["answer"] = response
                post_data["challengeId"] = challenge
                post_data["type"] = "0"

            json_res = self.api_request(
                "https://safelinking.net/v1/captcha", post_data
            )

            # Evaluate response
            if json_res is None:
                self.fail(self._("Invalid JSON response"))

            # Response: Wrong password
            elif "passwordFail" in json_res:
                self.log_error(
                    self._('Wrong password: "{}"').format(self.package_password)
                )
                self.fail(self._("Wrong password"))

            elif "captchaFail" in json_res:
                self.retry_captcha()

            # Response: Error message
            elif "message" in json_res:
                self.log_error(self._("Site error: {}").format(json_res["message"]))
                self.retry(wait=60, msg=json_res["message"])

            # Response: Links
            elif "links" in json_res:
                for link in json_res["links"]:
                    self.links.append(link["url"])

            else:
                self.fail(self._("Unexpected JSON response"))
