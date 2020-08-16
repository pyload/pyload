# -*- coding: utf-8 -*-

import re
from datetime import timedelta

from pyload.core.utils import seconds

from ..anticaptchas.ReCaptcha import ReCaptcha
from ..base.downloader import BaseDownloader


class FreakshareCom(BaseDownloader):
    __name__ = "FreakshareCom"
    __type__ = "downloader"
    __version__ = "0.49"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?freakshare\.(net|com)/files/\S*?/"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """Freakshare.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("sitacuisses", "sitacuisses@yahoo.de"),
        ("spoob", "spoob@pyload.net"),
        ("mkaay", "mkaay@mkaay.de"),
        ("Toilal", "toilal.dev@gmail.com"),
    ]

    def setup(self):
        self.multi_dl = False
        self.req_opts = []

    def process(self, pyfile):
        self.pyfile = pyfile

        pyfile.url = pyfile.url.replace("freakshare.net/", "freakshare.com/")

        if self.account:
            self.data = self.load(pyfile.url, cookies=False)
            pyfile.name = self.get_file_name()
            self.download(pyfile.url)

        else:
            self.prepare()
            self.get_file_url()

            self.download(pyfile.url, post=self.req_opts)

            check = self.scan_download(
                {
                    "bad": "bad try",
                    "paralell": "> Sorry, you cant download more then 1 files at time. <",
                    "empty": "Warning: Unknown: Filename cannot be empty",
                    "wrong_captcha": "Wrong Captcha!",
                    "downloadserver": "No Downloadserver. Please try again later!",
                }
            )

            if check == "bad":
                self.fail(self._("Bad Try"))

            elif check == "paralell":
                self.wait(300, True)
                self.retry()

            elif check == "empty":
                self.fail(self._("File not downloadable"))

            elif check == "wrong_captcha":
                self.retry_captcha()

            elif check == "downloadserver":
                self.retry(
                    5, timedelta(minutes=15).seconds, self._("No Download server")
                )

    def prepare(self):
        pyfile = self.pyfile

        self.download_html()

        if not self.file_exists():
            self.offline()

        self.set_wait(self.get_waiting_time())

        pyfile.name = self.get_file_name()
        pyfile.size = self.get_file_size()

        self.wait()

        return True

    def download_html(self):
        #: Set english language in server session
        self.load("http://freakshare.com/index.php", {"language": "EN"})
        self.data = self.load(self.pyfile.url)

    def get_file_url(self):
        """
        Returns the absolute downloadable filepath.
        """
        if not self.data:
            self.download_html()
        if not self.want_reconnect:
            #: Get the Post options for the Request
            self.req_opts = self.get_download_options()
            # file_url = self.pyfile.url
            # return file_url
        else:
            self.offline()

    def get_file_name(self):
        if not self.data:
            self.download_html()

        if not self.want_reconnect:
            m = re.search(
                r"<h1\sclass=\"box_heading\"\sstyle=\"text-align:center;\">([^ ]+)",
                self.data,
            )
            if m is not None:
                file_name = m.group(1)
            else:
                file_name = self.pyfile.url

            return file_name
        else:
            return self.pyfile.url

    def get_file_size(self):
        size = 0
        if not self.data:
            self.download_html()

        if not self.want_reconnect:
            m = re.search(
                r"<h1\sclass=\"box_heading\"\sstyle=\"text-align:center;\">[^ ]+ - ([^ ]+) (\w\w)yte",
                self.data,
            )
            if m is not None:
                units = float(m.group(1).replace(",", ""))
                pow = {"KB": 1, "MB": 2, "GB": 3}[m.group(2)]
                size = int(units << 10 ** pow)

        return size

    def get_waiting_time(self):
        if not self.data:
            self.download_html()

        if "Your Traffic is used up for today" in self.data:
            self.want_reconnect = True
            return seconds.to_midnight()

        timestring = re.search(
            r"\s*var\s(?:downloadWait|time)\s=\s(\d*)[\d.]*;", self.data
        )
        if timestring:
            return int(timestring.group(1))
        else:
            return 60

    def file_exists(self):
        """
        Returns True or False.
        """
        if not self.data:
            self.download_html()
        if re.search(r"This file does not exist!", self.data):
            return False
        else:
            return True

    def get_download_options(self):
        re_envelope = re.search(
            r".*?value=\"Free\sDownload\".*?\n*?(.*?<.*?>\n*)*?\n*\s*?</form>",
            self.data,
        ).group(
            0
        )  #: Get the whole request
        to_sort = re.findall(
            r"<input\stype=\"hidden\"\svalue=\"(.*?)\"\sname=\"(.*?)\"\s\/>",
            re_envelope,
        )
        request_options = {n: v for (v, n) in to_sort}

        herewego = self.load(
            self.pyfile.url, None, request_options
        )  #: The actual download-Page

        to_sort = re.findall(
            r"<input\stype=\".*?\"\svalue=\"(\S*?)\".*?name=\"(\S*?)\"\s.*?\/>",
            herewego,
        )
        request_options = {n: v for (v, n) in to_sort}

        challenge = re.search(
            r"http://api\.recaptcha\.net/challenge\?k=(\w+)", herewego
        )

        if challenge:
            re_captcha = ReCaptcha(self.pyfile)
            (
                request_options["recaptcha_challenge_field"],
                request_options["recaptcha_response_field"],
            ) = re_captcha.challenge(challenge.group(1))

        return request_options
