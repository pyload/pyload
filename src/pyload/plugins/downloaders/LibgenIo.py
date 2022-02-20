# -*- coding: utf-8 -*-

import json
import re
import time
import urllib.parse

from bs4 import BeautifulSoup
from pyload.core.network.http.exceptions import BadHeader

from ..base.downloader import BaseDownloader


class LibgenIo(BaseDownloader):
    __name__ = "LibgenIo"
    __type__ = "downloader"
    __version__ = "0.71"
    __status__ = "testing"

    # Only for libgen hosts and URLs that have an MD5
    __pattern__ = r"(?i)https?://([^/]+\.)?(libgen\.io|libgen\.me|booksdescr\.org|booksdl\.org|booksdescr\.com|lib1\.org|library1\.org|libgen\.pw|gen\.lib\.rus\.ec)/.*"
    __config__ = [
        ("enabled", "enabled", "Activated", True),
        (
            "mirrors",
            "string",
            "Libgen mirror URL patterns (space-separated)",
            "http://booksdl.org/{topiclong}/get.php?md5={md5} http://booksdl.org/get.php?md5={md5}",
        ),
        ("query_api", "bool", "Query libgen API to fetch more book details", False),
        (
            "api_mirrors",
            "string",
            "API mirror URLs (space-separated)",
            "http://libgen.io/json.php http://booksdescr.org/json.php",
        ),
        (
            "api_fields",
            "string",
            "API fields to fetch",
            "id,authorfamily1,authorname1,series1,extension,language,pages,isbn,year",
        ),
        ("max_recursions", "int", "Maximum directories to recurse into", 100),
    ]

    __description__ = """Plugin for libgen.io, respecting throttling, bypassing ad screen, and recursing through folders"""
    __license__ = "GPLv3"
    __authors__ = [("Yann Jouanique", "yann.jouanique@gmail.com")]

    def setup(self):
        self.chunk_limit = -1
        self.resume_download = True
        self.multi_dl = False

    def libgen_api(self, topic, md5):
        get_params = {
            "lg_topic": topic,
            "md5": md5,
            "fields": self.config.get("api_fields"),
        }

        # Loop through mirrors
        mirrors = self.config.get("api_mirrors").split()
        resp = []

        for url in mirrors:
            self.log_debug("Trying API mirror: " + url)
            try:
                res = self.load(url, get=get_params)
                self.log_debug("Raw API response: {}".format(res))
                resp = json.loads(res)
                self.log_debug("Parsed API response: {}".format(resp))
                if resp and len(resp) > 0 and "id" in resp[0]:
                    self.log_debug("Got book details: {}".format(resp[0]))
                    return resp[0]
            except:
                self.log_debug("Error calling libgen API at {}".format(url))

        self.log_debug("No working API results")
        return {}

    def get_book_info(self, url):
        self.log_debug("Getting book info for URL {}".format(url))
        info = {"url": url}
        match = re.search(r"(?i)(?:/|md5=)(?P<md5>[a-f0-9]{32})\b", url)

        if not match:
            self.log_error("Could not extract MD5 from URL " + url)

        else:
            info["md5"] = match.group("md5")
            topic = ""
            topicmatch = re.search(
                r"(?i)\b(fiction|foreignfiction|comics|scimag)\b", url
            )
            if topicmatch and topicmatch.group():
                topic = topicmatch.group()

            info["topic"] = topic
            info["topicshort"] = re.sub(r"^foreign", "", topic)
            info["topiclong"] = re.sub(r"^fiction", "foreignfiction", topic)

            # enrich with API call?
            if self.config.get("query_api"):
                self.log_debug("Enriching book info by calling libgen API")
                api_info = self.libgen_api(info["topicshort"], info["md5"])
                if api_info and api_info["id"]:
                    # Add all info from API response... this will override any existing keys...
                    info.update(api_info)

            self.log_debug("File info for this download: {}".format(info))

        return info

    def process(self, pyfile):
        url = re.sub(r"^(jd|py)", "http", pyfile.url)
        self.log_debug("Start LibGen process for URL {}".format(url))
        self.log_debug("Using download folder {}".format(pyfile.package().folder))

        # Check if it's an md5 link (single download from the structured archive) or an unsorted comic
        if re.search(r"/comics0/", url):
            # It's an unsorted comic, download file or recurse through folder...
            self.log_debug("This seems to be an unsorted comics link")
            self.processComic(pyfile)
            return

        # Get file info
        self.log_debug("Detecting type for non-Comic URL {}".format(url))
        bookinfo = self.get_book_info(pyfile.url)
        if not bookinfo["md5"]:
            self.fail("Unrecognizable URL")
            return

        # Loop through mirrors
        found = False
        mirrors = self.config.get("mirrors").split()

        for mirror in mirrors:
            url = mirror.format(**bookinfo)
            self.log_debug("Trying mirror: " + url)
            for _i in range(2):
                try:
                    self.log_debug("Download attempt " + str(_i))
                    self.download(url, disposition=True)
                    self.log_debug("Response: {:d}".format(self.req.code))

                except BadHeader as e:
                    if e.code not in (400, 401, 403, 404, 410, 500, 503):
                        raise

                if self.req.code in (400, 404, 410):
                    self.log_warning("Not found on this mirror, skipping")
                    break

                elif self.req.code in (500, 503):
                    self.log_warning("Temporary server error, retrying...")
                    time.sleep(5)

                else:
                    self.log_debug("Download successful")
                    found = True
                    break

            # Stop mirror iteration if success
            if found:
                break

        # End of the loop!
        if not found:
            self.log_error("Could not find a working mirror")
            self.fail("No working mirror")

        else:
            self.log_debug("End of download loop, checking download")
            self.check_download()

    def check_download(self):
        errmsg = self.scan_download(
            {
                "Html error": re.compile(
                    rb"\A(?:\s*<.+>)?((?:[\w\s]*(?:error)\s*\:?)?\s*\d{3})(?:\Z|\s+)"
                ),
                "Html file": re.compile(rb"\A\s*<!DOCTYPE html"),
                "Request error": re.compile(
                    rb"an error occured while processing your request"
                ),
            }
        )

        if not errmsg:
            return

        try:
            errmsg += " | " + self.last_check.group(1).strip()

        except Exception:
            pass

        self.log_warning("Check result: {}, Waiting 1 minute and retry".format(errmsg))
        self.retry(3, 60, errmsg)

    def processComic(self, pyfile):
        url = re.sub(r"^(jd|py)", "http", pyfile.url)

        if not re.match(r".*\/$", url):
            # It's a single direct download link, donwload it
            self.log_debug("Link is a single file")
            for _i in range(2):
                try:
                    self.download(url, ref=False, disposition=True)
                except BadHeader as e:
                    if e.code not in (401, 403, 404, 410):
                        raise

                if self.req.code in (404, 410):
                    self.offline()
                else:
                    break

            self.check_download()

        else:
            # It's a directory list, parse the list
            self.log_debug("Link is a directory")
            max = self.config.get("max_recursions")

            html = self.load(pyfile.url, decode=True)
            self.log_debug("Got raw HTML page = " + html)
            if html:
                soup = BeautifulSoup(html, "html.parser")
                if soup:
                    self.log_debug("Got HTML page - Title = " + soup.title.string)
                    domain = urllib.parse.urlparse(pyfile.url).netloc.lower()

                    # Get all links, excluding parent folder
                    for link in soup.findAll("a", href=re.compile(r"^(?!\.\./).*")):
                        nlinks = len(pyfile.package().getChildren())
                        if nlinks >= max:
                            self.log_warning(
                                "Reached max link count for this package ({}/{}), skipping".format(
                                    nlinks, max
                                )
                            )
                            break

                        self.log_debug("Detected new link")

                        href = link.get("href")
                        self.log_debug("href: " + href)

                        abslink = urllib.parse.urljoin(pyfile.url, href)
                        self.log_debug("Abslink: " + abslink)

                        new_domain = urllib.parse.urlparse(abslink).netloc.lower()
                        self.log_debug("Domain: " + new_domain)

                        if new_domain != domain:
                            self.log_debug("Different domain, ignoring link...")
                            break

                        self.log_debug("Adding link " + abslink)
                        self.pyload.api.addFiles(pyfile.package().id, [abslink])

            # Ignore this link as it's a directory page
            self.skip("Link was a directory listing")
