# -*- coding: utf-8 -*-

import re

from time import sleep, time

from module.network.RequestFactory import getURL
from module.plugins.Hoster import Hoster
from module.plugins.Plugin import chunks


def getInfo(urls):
    ##  returns list of tupels (name, size (in bytes), status (see FileDatabase), url)

    apiurl = "http://api.netload.in/info.php?auth=Zf9SnQh9WiReEsb18akjvQGqT0I830e8&bz=1&md5=1&file_id="
    id_regex = re.compile(NetloadIn.__pattern__)
    urls_per_query = 80

    for chunk in chunks(urls, urls_per_query):
        ids = ""
        for url in chunk:
            match = id_regex.search(url)
            if match:
                ids = ids + match.group(1) + ";"

        api = getURL(apiurl + ids, decode=True)

        if api is None or len(api) < 10:
            print "Netload prefetch: failed "
            return
        if api.find("unknown_auth") >= 0:
            print "Netload prefetch: Outdated auth code "
            return

        result = []

        for i, r in enumerate(api.splitlines()):
            try:
                tmp = r.split(";")
                try:
                    size = int(tmp[2])
                except:
                    size = 0
                result.append((tmp[1], size, 2 if tmp[3] == "online" else 1, chunk[i]))
            except:
                print "Netload prefetch: Error while processing response: "
                print r

        yield result


class NetloadIn(Hoster):
    __name__ = "NetloadIn"
    __type__ = "hoster"
    __version__ = "0.45"

    __pattern__ = r'https?://(?:[^/]*\.)?netload\.in/(?:datei(.*?)(?:\.htm|/)|index.php?id=10&file_id=)'

    __description__ = """Netload.in hoster plugin"""
    __author_name__ = ("spoob", "RaNaN", "Gregy")
    __author_mail__ = ("spoob@pyload.org", "ranan@pyload.org", "gregy@gregy.cz")


    def setup(self):
        self.multiDL = self.resumeDownload = self.premium

    def process(self, pyfile):
        self.url = pyfile.url
        self.prepare()
        pyfile.setStatus("downloading")
        self.proceed(self.url)

    def prepare(self):
        self.download_api_data()

        if self.api_data and self.api_data['filename']:
            self.pyfile.name = self.api_data['filename']

        if self.premium:
            self.logDebug("Netload: Use Premium Account")
            settings = self.load("http://www.netload.in/index.php?id=2&lang=en")
            if '<option value="2" selected="selected">Direkter Download' in settings:
                self.logDebug("Using direct download")
                return True
            else:
                self.logDebug("Direct downloads not enabled. Parsing html for a download URL")

        if self.download_html():
            return True
        else:
            self.fail("Failed")
            return False

    def download_api_data(self, n=0):
        url = self.url
        id_regex = re.compile(self.__pattern__)
        match = id_regex.search(url)

        if match:
            #normalize url
            self.url = 'http://www.netload.in/datei%s.htm' % match.group(1)
            self.logDebug("URL: %s" % self.url)
        else:
            self.api_data = False
            return

        apiurl = "http://api.netload.in/info.php"
        src = self.load(apiurl, cookies=False,
                        get={"file_id": match.group(1), "auth": "Zf9SnQh9WiReEsb18akjvQGqT0I830e8", "bz": "1",
                             "md5": "1"}, decode=True).strip()
        if not src and n <= 3:
            sleep(0.2)
            self.download_api_data(n + 1)
            return

        self.logDebug("Netload: APIDATA: " + src)
        self.api_data = {}
        if src and ";" in src and src not in ("unknown file_data", "unknown_server_data", "No input file specified."):
            lines = src.split(";")
            self.api_data['exists'] = True
            self.api_data['fileid'] = lines[0]
            self.api_data['filename'] = lines[1]
            self.api_data['size'] = lines[2]
            self.api_data['status'] = lines[3]
            if self.api_data['status'] == "online":
                self.api_data['checksum'] = lines[4].strip()
            else:
                self.api_data = False  # check manually since api data is useless sometimes

            if lines[0] == lines[1] and lines[2] == "0":  # useless api data
                self.api_data = False
        else:
            self.api_data = False

    def final_wait(self, page):
        wait_time = self.get_wait_time(page)
        self.setWait(wait_time)
        self.logDebug("Netload: final wait %d seconds" % wait_time)
        self.wait()
        self.url = self.get_file_url(page)

    def download_html(self):
        self.logDebug("Netload: Entering download_html")
        page = self.load(self.url, decode=True)
        t = time() + 30

        if "/share/templates/download_hddcrash.tpl" in page:
            self.logError("Netload HDD Crash")
            self.fail(_("File temporarily not available"))

        if not self.api_data:
            self.logDebug("API Data may be useless, get details from html page")

            if "* The file was deleted" in page:
                self.offline()

            name = re.search(r'class="dl_first_filename">([^<]+)', page, re.MULTILINE)
            # the found filename is not truncated
            if name:
                name = name.group(1).strip()
                if not name.endswith(".."):
                    self.pyfile.name = name

        captchawaited = False
        for i in xrange(10):

            if not page:
                page = self.load(self.url)
                t = time() + 30

            if "/share/templates/download_hddcrash.tpl" in page:
                self.logError("Netload HDD Crash")
                self.fail(_("File temporarily not available"))

            self.logDebug("Netload: try number %d " % i)

            if ">Your download is being prepared.<" in page:
                self.logDebug("Netload: We will prepare your download")
                self.final_wait(page)
                return True
            if ">An access request has been made from IP address <" in page:
                wait = self.get_wait_time(page)
                if not wait:
                    self.logDebug("Netload: Wait was 0 setting 30")
                    wait = 30 * 60
                self.logInfo(_("Netload: waiting between downloads %d s." % wait))
                self.wantReconnect = True
                self.setWait(wait)
                self.wait()

                return self.download_html()

            self.logDebug("Netload: Trying to find captcha")

            try:
                url_captcha_html = "http://netload.in/" + re.search('(index.php\?id=10&amp;.*&amp;captcha=1)',
                                                                    page).group(1).replace("amp;", "")
            except:
                page = None
                continue

            try:
                page = self.load(url_captcha_html, cookies=True)
                captcha_url = "http://netload.in/" + re.search('(share/includes/captcha.php\?t=\d*)', page).group(1)
            except:
                self.logDebug("Netload: Could not find captcha, try again from beginning")
                captchawaited = False
                continue

            file_id = re.search('<input name="file_id" type="hidden" value="(.*)" />', page).group(1)
            if not captchawaited:
                wait = self.get_wait_time(page)
                if i == 0:
                    self.pyfile.waitUntil = time()  # dont wait contrary to time on website
                else:
                    self.pyfile.waitUntil = t
                self.logInfo(_("Netload: waiting for captcha %d s.") % (self.pyfile.waitUntil - time()))
                #self.setWait(wait)
                self.wait()
                captchawaited = True

            captcha = self.decryptCaptcha(captcha_url)
            page = self.load("http://netload.in/index.php?id=10", post={"file_id": file_id, "captcha_check": captcha},
                             cookies=True)

        return False

    def get_file_url(self, page):
        try:
            file_url_pattern = r"<a class=\"Orange_Link\" href=\"(http://.+)\".?>Or click here"
            attempt = re.search(file_url_pattern, page)
            if attempt is not None:
                return attempt.group(1)
            else:
                self.logDebug("Netload: Backup try for final link")
                file_url_pattern = r"<a href=\"(.+)\" class=\"Orange_Link\">Click here"
                attempt = re.search(file_url_pattern, page)
                return "http://netload.in/" + attempt.group(1)
        except:
            self.logDebug("Netload: Getting final link failed")
            return None

    def get_wait_time(self, page):
        wait_seconds = int(re.search(r"countdown\((.+),'change\(\)'\)", page).group(1)) / 100
        return wait_seconds

    def proceed(self, url):
        self.logDebug("Netload: Downloading..")

        self.download(url, disposition=True)

        check = self.checkDownload({"empty": re.compile(r"^$"), "offline": re.compile("The file was deleted")})

        if check == "empty":
            self.logInfo(_("Downloaded File was empty"))
            self.retry()
        elif check == "offline":
            self.offline()
