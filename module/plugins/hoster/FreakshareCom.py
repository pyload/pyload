# -*- coding: utf-8 -*-

import re

from module.plugins.Hoster import Hoster
from module.plugins.hoster.UnrestrictLi import secondsToMidnight
from module.plugins.internal.CaptchaService import ReCaptcha


class FreakshareCom(Hoster):
    __name__ = "FreakshareCom"
    __type__ = "hoster"
    __version__ = "0.39"

    __pattern__ = r'http://(?:www\.)?freakshare\.(net|com)/files/\S*?/'

    __description__ = """Freakshare.com hoster plugin"""
    __author_name__ = ("sitacuisses", "spoob", "mkaay", "Toilal")
    __author_mail__ = ("sitacuisses@yahoo.de", "spoob@pyload.org", "mkaay@mkaay.de", "toilal.dev@gmail.com")


    def setup(self):
        self.multiDL = False
        self.req_opts = []

    def process(self, pyfile):
        self.pyfile = pyfile

        pyfile.url = pyfile.url.replace("freakshare.net/", "freakshare.com/")

        if self.account:
            self.html = self.load(pyfile.url, cookies=False)
            pyfile.name = self.get_file_name()
            self.download(pyfile.url)

        else:
            self.prepare()
            self.get_file_url()

            self.download(pyfile.url, post=self.req_opts)

            check = self.checkDownload({"bad": "bad try",
                                        "paralell": "> Sorry, you cant download more then 1 files at time. <",
                                        "empty": "Warning: Unknown: Filename cannot be empty",
                                        "wrong_captcha": "Wrong Captcha!",
                                        "downloadserver": "No Downloadserver. Please try again later!"})

            if check == "bad":
                self.fail("Bad Try.")
            elif check == "paralell":
                self.setWait(300, True)
                self.wait()
                self.retry()
            elif check == "empty":
                self.fail("File not downloadable")
            elif check == "wrong_captcha":
                self.invalidCaptcha()
                self.retry()
            elif check == "downloadserver":
                self.retry(5, 15 * 60, "No Download server")

    def prepare(self):
        pyfile = self.pyfile

        self.wantReconnect = False

        self.download_html()

        if not self.file_exists():
            self.offline()

        self.setWait(self.get_waiting_time())

        pyfile.name = self.get_file_name()
        pyfile.size = self.get_file_size()

        self.wait()

        return True

    def download_html(self):
        self.load("http://freakshare.com/index.php", {"language": "EN"})  # Set english language in server session
        self.html = self.load(self.pyfile.url)

    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        if not self.html:
            self.download_html()
        if not self.wantReconnect:
            self.req_opts = self.get_download_options()  # get the Post options for the Request
            #file_url = self.pyfile.url
            #return file_url
        else:
            self.offline()

    def get_file_name(self):
        if not self.html:
            self.download_html()
        if not self.wantReconnect:
            file_name = re.search(r"<h1\sclass=\"box_heading\"\sstyle=\"text-align:center;\">([^ ]+)", self.html)
            if file_name is not None:
                file_name = file_name.group(1)
            else:
                file_name = self.pyfile.url
            return file_name
        else:
            return self.pyfile.url

    def get_file_size(self):
        size = 0
        if not self.html:
            self.download_html()
        if not self.wantReconnect:
            file_size_check = re.search(
                r"<h1\sclass=\"box_heading\"\sstyle=\"text-align:center;\">[^ ]+ - ([^ ]+) (\w\w)yte", self.html)
            if file_size_check is not None:
                units = float(file_size_check.group(1).replace(",", ""))
                pow = {'KB': 1, 'MB': 2, 'GB': 3}[file_size_check.group(2)]
                size = int(units * 1024 ** pow)

        return size

    def get_waiting_time(self):
        if not self.html:
            self.download_html()

        if "Your Traffic is used up for today" in self.html:
            self.wantReconnect = True
            return secondsToMidnight(gmt=2)

        timestring = re.search('\s*var\s(?:downloadWait|time)\s=\s(\d*)[.\d]*;', self.html)
        if timestring:
            return int(timestring.group(1)) + 1  # add 1 sec as tenths of seconds are cut off
        else:
            return 60

    def file_exists(self):
        """ returns True or False
        """
        if not self.html:
            self.download_html()
        if re.search(r"This file does not exist!", self.html) is not None:
            return False
        else:
            return True

    def get_download_options(self):
        re_envelope = re.search(r".*?value=\"Free\sDownload\".*?\n*?(.*?<.*?>\n*)*?\n*\s*?</form>",
                                self.html).group(0)  # get the whole request
        to_sort = re.findall(r"<input\stype=\"hidden\"\svalue=\"(.*?)\"\sname=\"(.*?)\"\s\/>", re_envelope)
        request_options = dict((n, v) for (v, n) in to_sort)

        herewego = self.load(self.pyfile.url, None, request_options)  # the actual download-Page

        # comment this in, when it doesnt work
        # with open("DUMP__FS_.HTML", "w") as fp:
        # fp.write(herewego)

        to_sort = re.findall(r"<input\stype=\".*?\"\svalue=\"(\S*?)\".*?name=\"(\S*?)\"\s.*?\/>", herewego)
        request_options = dict((n, v) for (v, n) in to_sort)

        # comment this in, when it doesnt work as well
        #print "\n\n%s\n\n" % ";".join(["%s=%s" % x for x in to_sort])

        challenge = re.search(r"http://api\.recaptcha\.net/challenge\?k=([0-9A-Za-z]+)", herewego)

        if challenge:
            re_captcha = ReCaptcha(self)
            (request_options['recaptcha_challenge_field'],
             request_options['recaptcha_response_field']) = re_captcha.challenge(challenge.group(1))

        return request_options
