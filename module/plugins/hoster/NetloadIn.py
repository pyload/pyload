#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from time import sleep

from module.plugins.Hoster import Hoster
from module.network.Request import getURL

def getInfo(urls):
 ##  returns list of tupels (name, size (in bytes), status (see FileDatabase), url)


    apiurl = "http://api.netload.in/info.php?auth=Zf9SnQh9WiReEsb18akjvQGqT0I830e8&bz=1&md5=1&file_id="
    id_regex = re.compile("http://.*netload\.in/(?:datei(.*?)(?:\.htm|/)|index.php?id=10&file_id=)")
    urls_per_query = 80

    iterations = len(urls)/urls_per_query
    if len(urls)%urls_per_query > 0:
        iterations = iterations +1

    for i in range(iterations):
        ids = ""
        for url in urls[i*urls_per_query:(i+1)*urls_per_query]:
            match = id_regex.search(url)
            if match:
                ids = ids + match.group(1) +";"

        api = getURL(apiurl+ids)

        if api == None or len(api) < 10:
            print "Netload prefetch: failed "
            return
        if api.find("unknown_auth") >= 0:
            print "Netload prefetch: Outdated auth code "
            return

        result = []

        counter = 0
        for r in api.split():
            try:
                tmp = r.split(";")
                try:
                    size = int(tmp[2])
                except:
                    size = 0
                result.append( (tmp[1], size, 2 if tmp[3] == "online" else 1, urls[(i*80)+counter]) )
            except:
                print "Netload prefetch: Error while processing response: "
                print r
            counter = counter +1

        yield result

class NetloadIn(Hoster):
    __name__ = "NetloadIn"
    __type__ = "hoster"
    __pattern__ = r"http://.*netload\.in/(?:datei(.*?)(?:\.htm|/)|index.php?id=10&file_id=)"
    __version__ = "0.2"
    __description__ = """Netload.in Download Hoster"""
    __config__ = [ ("dumpgen", "bool", "Generate debug page dumps on stdout", "False") ]
    __author_name__ = ("spoob", "RaNaN", "Gregy")
    __author_mail__ = ("spoob@pyload.org", "ranan@pyload.org", "gregy@gregy.cz")

    def setup(self):
        self.multiDL = False
        if self.account:
            self.multiDL = True
            self.req.canContinue = True
    
    def process(self, pyfile):
        self.url = pyfile.url
        self.prepare()
        self.pyfile.setStatus("downloading")
        self.proceed(self.url)

    def getInfo(self):
        self.log.debug("Netload: Info prefetch")
        self.download_api_data()
        if self.api_data and self.api_data["filename"]:
            self.pyfile.name = self.api_data["filename"]
            self.pyfile.sync()

    def prepare(self):
        self.download_api_data()

        if self.api_data and self.api_data["filename"]:
            self.pyfile.name = self.api_data["filename"]

        if self.account:
            self.log.debug("Netload: Use Premium Account")
            return True

        if self.download_html():
            return True
        else:
            self.fail("Failed")
            return False
            
    def download_api_data(self):
        url = self.url
        id_regex = re.compile("http://.*netload\.in/(?:datei(.*?)(?:\.htm|/)|index.php?id=10&file_id=)")
        match = id_regex.search(url)
        if match:
            apiurl = "http://netload.in/share/fileinfos2.php"
            src = self.load(apiurl, cookies=False, get={"file_id": match.group(1)})
            self.log.debug("Netload: APIDATA: "+src.strip())
            self.api_data = {}
            if src == "unknown_server_data":
                self.api_data = False
            elif not src == "unknown file_data":
                
                lines = src.split(";")
                self.api_data["exists"] = True
                self.api_data["fileid"] = lines[0]
                self.api_data["filename"] = lines[1]
                self.api_data["size"] = lines[2] #@TODO formatting? (ex: '2.07 KB')
                self.api_data["status"] = lines[3]
                if self.api_data["status"] == "online":
                    self.api_data["checksum"] = lines[4].strip()
                else:
                    self.offline();
            else:
                self.api_data["exists"] = False
        else:
            self.api_data = False
            self.html[0] = self.load(self.url, cookies=False)

    def final_wait(self, page):
        wait_time = self.get_wait_time(page)
        self.setWait(wait_time)
        self.log.debug(_("Netload: final wait %d seconds" % wait_time))
        self.wait()
        self.url = self.get_file_url(page)

    def download_html(self):
        self.log.debug("Netload: Entering download_html")
        page = self.load(self.url, cookies=True)
        captchawaited = False
        for i in range(10):
            self.log.debug(_("Netload: try number %d " % i))
            if self.getConf('dumpgen'):
                print page

            if re.search(r"(We will prepare your download..)", page) != None:
                self.log.debug("Netload: We will prepare your download")
                self.final_wait(page);
                return True
            if re.search(r"(We had a reqeust with the IP)", page) != None:
                wait = self.get_wait_time(page);
                if wait == 0:
                    self.log.debug("Netload: Wait was 0 setting 30")
                    wait = 30
                self.log.info(_("Netload: waiting between downloads %d s." % wait))
                self.setWait(wait)
                self.wait()

                link = re.search(r"You can download now your next file. <a href=\"(index.php\?id=10&amp;.*)\" class=\"Orange_Link\">Click here for the download</a>", page)
                if link != None:
                    self.log.debug("Netload: Using new link found on page")
                    page = self.load("http://netload.in/" + link.group(1).replace("amp;", ""))
                else:
                    self.log.debug("Netload: No new link found, using old one")
                    page = self.load(self.url, cookies=True)
                continue

            
            self.log.debug("Netload: Trying to find captcha")

            url_captcha_html = "http://netload.in/" + re.search('(index.php\?id=10&amp;.*&amp;captcha=1)', page).group(1).replace("amp;", "")
            page = self.load(url_captcha_html, cookies=True)

            try:
                captcha_url = "http://netload.in/" + re.search('(share/includes/captcha.php\?t=\d*)', page).group(1)
            except:
                open("dump.html", "w").write(page)
                self.log.debug("Netload: Could not find captcha, try again from begining")
                continue

            file_id = re.search('<input name="file_id" type="hidden" value="(.*)" />', page).group(1)
            if not captchawaited:
                wait = self.get_wait_time(page);
                self.log.info(_("Netload: waiting for captcha %d s." % wait))
                self.setWait(wait)
                self.wait()
                captchawaited = True

            captcha = self.decryptCaptcha(captcha_url)
            sleep(4)
            page = self.load("http://netload.in/index.php?id=10", post={"file_id": file_id, "captcha_check": captcha}, cookies=True)

        return False
        

    def get_file_url(self, page):
        try:
            file_url_pattern = r"<a class=\"Orange_Link\" href=\"(http://.+)\" >Click here"
            attempt = re.search(file_url_pattern, page)
            if attempt != None:
                return attempt.group(1)
            else:
                self.log.debug("Netload: Backup try for final link")
                file_url_pattern = r"<a href=\"(.+)\" class=\"Orange_Link\">Click here"
                attempt = re.search(file_url_pattern, page)
                return "http://netload.in/"+attempt.group(1);
        except:
            self.log.debug("Netload: Getting final link failed")
            return None

    def get_wait_time(self, page):
        wait_seconds = int(re.search(r"countdown\((.+),'change\(\)'\)", page).group(1)) / 100
        return wait_seconds
        

    def proceed(self, url):
        self.log.debug("Netload: Downloading..")
        if self.account:
            self.req.load("http://netload.in/index.php", None, { "txtuser" : self.config['username'], "txtpass" : self.config['password'], "txtcheck" : "login", "txtlogin" : ""}, cookies=True)
        self.download(url, cookies=True)

