# -*- coding: utf-8 -*-

# TODO dont trust online status, can be offline
# only trust offline status?

# TODO prefer new releases
# old releases can have missing parts

# TODO prefer "complete" series
# example:
# https://serienfans.org/south-park
# example complete:
# Staffel 24 Complete 1080p | 5.9 GB
# <h3><label class="opn" for="se2820259829056"></label>Staffel24<div class="complete"><span>Complete</span></div><span class="morespec">1080p | 5.9GB</span><span class="audiotag"><img src="/images/DE.svg"><img src="/images/EN.svg"></span><span class="grouptag">JaJunge</span></h3>
# example incomplete: "2 4" means "2 of 4 episodes"
# Staffel 24 2 4 720p | 921.7 MB
# <h3><label class="opn" for="se1525622736550"></label>Staffel24<div class="complete"><span>2</span><span>4</span></div><span class="morespec">720p | 921.7MB</span><span class="audiotag"><img src="/images/DE.svg"><img src="/images/EN.svg"></span><span class="grouptag">JaJunge</span></h3>

#
# Test links:
#   https://serienfans.org/breaking-bad

import base64
import re
import urllib.parse
import time
import json

from bs4 import BeautifulSoup

if __name__ == "__main__":
    import os
    import sys
    # fix: ModuleNotFoundError: No module named 'pyload'
    sys.path.insert(0, os.path.dirname(__file__) + "/../../..")

from pyload.core.network.http.http_request import HTTPRequest
from pyload.plugins.base.decrypter import BaseDecrypter
from pyload.core.network.http.exceptions import BadHeader


class SerienfansOrg(BaseDecrypter):
    __name__ = "SerienfansOrg"
    __type__ = "decrypter"
    __version__ = "0.1"
    __status__ = "testing"


    __pattern__ = r"https?://(?:www\.)?(?:serienfans|filmfans)\.org/[\w-]+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        # 720p is small and "good enough"
        # but 1080p releases seem to be better maintained, more up-to-date
        #("prefer_video_quality", "none;180p;240p;360p;480p;720p;1080p;2160p", "Prefer video quality", "1080p"),
        ("prefer_video_quality", "none;180p;240p;360p;480p;720p;1080p;2160p", "Prefer video quality", "none"),
        # TODO dont trust online status reported by serienfans
        ("use_first_online_hoster_only", "bool", "Use first online hoster only", False),
        # TODO implement ...
        # ("randomize_online_hosters", "bool", "Randomize online hosters", True),
        # ("prefer_hosters", "bool", "Prefer hosters", False),
        # ("prefer_hosters_list", "str", "Prefer hosters list", "rapidgator 1fichier katfile turbobit"),
        ("include_episode_links", "bool", "Include episode links", False),
        ("split_packages_by_hoster", "bool", "Split packages by hoster", True),
    ]

    __description__ = """Serienfans.org decrypter plugin"""
    __license__ = "MIT"
    __authors__ = [
        ("milahu", "milahu@gmail.com"),
    ]

    _is_serienfans = False
    _is_filmfans = False

    _write_cache = False
    _read_cache = False

    _response_1_cache = None
    _response_2_cache = None

    def setup(self):
        self.urls = []

        try:
            self.req.http.close()
        except Exception:
            pass

        self.req.http = HTTPRequest(
            cookies=self.req.cj,
            options=self.pyload.request_factory.get_options(),
            limit=2_000_000,
        )

    def decrypt(self, pyfile):

        self.pyfile = pyfile

        # self.log_debug(f"pyfile.status: {pyfile.status}")
        # raise 123

        # usually this is "serienfans.org" or "filmfans.org"
        self.pyfile_netloc = urllib.parse.urlparse(pyfile.url).netloc.lower()
        if self.pyfile_netloc.startswith("www."):
            self.pyfile_netloc = self.pyfile_netloc[4:]

        if self.pyfile_netloc == "serienfans.org":
            self._is_serienfans = True
        elif self.pyfile_netloc == "filmfans.org":
            self._is_filmfans = True
        else:
            # not reachable because of __pattern__
            self.log_error(f"bad netloc: {self.pyfile_netloc}")
            self.offline()
            return

        self._response_1_cache = self.pyload.tempdir + "/serienfans-cache-file-1.txt"
        self._response_2_cache = self.pyload.tempdir + "/serienfans-cache-file-2.txt"

        # fix: FilecryptCc: Folder is password protected
        # usually this is only needed for serienfans.org
        self.log_debug(f"setting password: {self.pyfile_netloc}")
        self.pyfile.package().password = self.pyfile_netloc

        response_1_text = self._get_response_text(pyfile.url, self._response_1_cache)

        # TODO check for http status 404
        if response_1_text == "Not Found":
            self.offline()
            return

        if self._is_serienfans:
            # initSeason('UQauKRVkdAM84pWBtMJSdAPe499YUzRr', 26, '', 'ALL');
            session_id_regex = r"initSeason\('([0-9a-zA-Z]+)', ([0-9]+), '', 'ALL'\);"
        elif self._is_filmfans:
            # initMovie('VSJKkEn8wAzkDtyqQVEvuXBMLnjdxDZz', '', '', '', '', '');
            session_id_regex = r"initMovie\('([0-9a-zA-Z]+)', '(.*?)', '(.*?)', '(.*?)', '(.*?)', '(.*?)'\);"

        session_id_match = re.search(session_id_regex, response_1_text)

        self.session_id = session_id_match.group(1)

        if self._is_serienfans:
            self.num_seasons = int(session_id_match.group(2))
        else:
            self.num_seasons = 1

        for season_num in range(1, 1 + self.num_seasons):
            self._decrypt_season(season_num)
            cache_path = self._response_2_cache
            if self._read_cache and os.path.exists(cache_path):
                # stop after first season
                break

    def _get_response_json(self, url, cache_path):
        return self._get_response_text(url, cache_path, decode_json=True)

    def _get_response_text(self, url, cache_path, decode_json=False):

        if callable(url):
            url = url()

        if self._read_cache and os.path.exists(cache_path):
            # read cache
            self.log_info(f"reading {cache_path}")
            with open(cache_path) as f:
                response_text = f.read()
            if decode_json:
                return json.loads(response_text)
            return response_text

        # fetch response

        retry_max = 10
        retry_step = 0
        response_data = None

        # retry loop
        while True:

            retry_step += 1

            try:
                response_text = self.load(url)

            except BadHeader as exc:
                # Bad server response: 400 Bad Request
                if retry_step == retry_max:
                    raise
                # else: retry
                self.log_debug(f"got BadHeader: {exc} -> retrying")
                time.sleep(3)
                continue

            if decode_json:
                try:
                    response_data = json.loads(response_text)
                    break # stop retry loop
                except json.decoder.JSONDecodeError:
                    if retry_step == retry_max:
                        raise Exception(f"got non-json response: {repr(response_text)[:1000]}")
                    # else: got html error page -> retry
                    self.log_debug(f"got non-json response: {repr(response_text)[:1000]} -> retrying")
                    time.sleep(3)
                    continue
            else:
                break # stop retry loop

        if self._write_cache:
            # write cache
            self.log_info(f"writing {cache_path}")
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            with open(cache_path, "w") as f:
                f.write(response_text)

        if decode_json:
            return response_data

        return response_text

    def _decrypt_season(self, season_num):

        # FIXME use some global rate-limiting
        # to allow decoding multiple serienfans.org urls in parallel
        # sleep between requests to avoid rate-limiting
        time.sleep(1)

        def get_request_url():
            request_time = int(time.time() * 1000)
            if self._is_serienfans:
                request_url = f"https://{self.pyfile_netloc}/api/v1/{self.session_id}/season/{season_num}?_={request_time}"
            else:
                request_url = f"https://{self.pyfile_netloc}/api/v1/{self.session_id}?_={request_time}"
            return request_url

        response_2_json = self._get_response_json(get_request_url, self._response_2_cache)

        self._decrypt_response_2(response_2_json)

    def _decrypt_response_2(self, response_2_json):

        self.log_info(f"response_2_json {repr(response_2_json)[:100]} ...")

        # response_2_json["qualitys"] # ["1080p", "480p", "720p"]
        # TODO filter by quality
        #   but only as a secondary filter after the movie + episode filter

        # response_2_json["bubblesQuality"] # ?

        # response_2_json["languages"] # ["DE", "EN"]
        # TODO filter by language
        #   but only as a secondary filter after the movie + episode filter

        # response_2_json["bubblesLanguage"] # ?

        response_2_html = response_2_json["html"]

        html_not_found = '\n Leider liegen zu dieser Staffel noch keine Einträge vor\n '
        if response_2_html == html_not_found:
            self.log_error("empty result")
            return

        # list of known release qualities
        release_quality_list = next(c for c in self.__config__ if c[0] == "prefer_video_quality")[1].split(";")[1:]
        # self.log_debug(f"release_quality_list {release_quality_list}")

        prefer_video_quality = self.config.get("prefer_video_quality")
        use_first_online_hoster_only = self.config.get("use_first_online_hoster_only")
        include_episode_links = self.config.get("include_episode_links")

        self.packages = []

        movie_soup = BeautifulSoup(response_2_html, "html.parser")

        # loop releases
        for release_entry in movie_soup.select("div.entry"):

            if self._is_serienfans:
                # release_entry: div.row, div.row, div.list.simple
                release_name = release_entry.select_one("small").text.strip()
            elif self._is_filmfans:
                release_name = release_entry.select_one("h3 > span").text.strip()

            self.log_info(f"package {release_name}")

            release_quality = None
            release_size = None

            if self._is_serienfans:
                # example: "480p | 1.3 GB"
                release_morespec = release_entry.select_one("div:nth-child(1) > div > h3 > span.morespec").text.strip()
                morespec_list = release_morespec.split(" | ")
                if len(morespec_list) >= 1:
                    release_quality = morespec_list[0].lower()
                if len(morespec_list) >= 2:
                    release_size = morespec_list[1]
                # release_audio = ?
                # example: "4SF"
                # release_grouptag = release_entry.select_one("div:nth-child(1) > div > h3 > span.grouptag").text.strip()
            elif self._is_filmfans:
                # parse key-value pairs
                release_info = dict()
                for audiotag in release_entry.select("span.audiotag"):
                    key = audiotag.select_one("small").text.strip()
                    if key[-1] == ":":
                        key = key[:-1]
                    # key = translate_key.get(key, key)
                    # print("audiotag.contents", audiotag.contents)
                    val = audiotag.contents[2].text.strip()
                    release_info[key] = val
                # self.log_debug(f"package {release_name}: release_info {release_info}")
                release_quality = release_info.get("Auflösung")
                if type(release_quality) == str:
                    release_quality = release_quality.lower()
                release_size = release_info.get("Größe")
                # release_audio = release_info.get("Audio")
                # release_grouptag = release_info.get("Releasegruppe")

            if not release_quality in release_quality_list:
                release_quality = None

            if (
                release_quality and
                prefer_video_quality != "none" and
                release_quality != prefer_video_quality
            ):
                self.log_debug(f"package {release_name}: skipping quality {release_quality} != {prefer_video_quality}")
                continue
                # TODO use other quality if the preferred quality is not available
                # first try better quality, then worse quality

            # start new package
            release_urls = []

            if self._is_serienfans:
                hoster_link_selector = "div:nth-child(2) > a"
            elif self._is_filmfans:
                hoster_link_selector = "div:nth-child(3) > a"

            # loop hosters
            self.log_debug(f"package {release_name}: looping hosters")
            for hoster_link in release_entry.select(hoster_link_selector):

                #self.log_debug(f"package {release_name}: hoster_link {hoster_link}")

                hoster_name = hoster_link.select_one("div > span").text.strip()
                # hoster_url returns redirect to filecrypt.co (etc)
                # hoster_url expires after some time

                # skip offline links
                link_online = True
                if hoster_link.select_one("i.st.off"):
                    link_online = False
                elif hoster_link.select_one("i.st.mix"):
                    # status: mixed
                    # only some links are online
                    link_online = None
                # elif hoster_link.select_one("i.st"):
                #    link_online = True
                #    # note: "status online" can be wrong

                if link_online == False:
                    # skip offline link
                    self.log_debug(f"package {release_name}: skipping offline hoster {hoster_name}")
                    continue

                link_status = "online" if link_online else "mixed"

                if use_first_online_hoster_only and link_online == None:
                    # skip mixed link
                    self.log_debug(f"package {release_name}: skipping mixed-online hoster: {hoster_name}")
                    continue

                hoster_url = "https://" + self.pyfile_netloc + hoster_link["href"]
                hoster_url = self._resolve_hoster_url(release_name, hoster_url)
                if not hoster_url:
                    continue

                self.log_info(f"package {release_name}: hoster {hoster_name} {link_status} {hoster_url}")
                release_urls.append((hoster_name, hoster_url))

                # break # debug: stop after first hoster_link

                if use_first_online_hoster_only and link_online == True:
                    # stop after first online link
                    self.log_debug(f"package {release_name}: using first online hoster only: {hoster_name}")
                    break

            self._add_release_urls(release_name, release_size, release_urls)
            release_urls = []

            if self._is_serienfans and include_episode_links:

                # add episode links to separate package
                release_urls = []
                package_name = release_name + " [episodes]"
                release_size = None

                # loop hosters
                # NOTE most download links are complete seasons
                for episode_div in release_entry.select("div.list.simple > div.row:not(.head)"):

                    episode_num = episode_div.select_one("div:nth-child(1)").text.strip() # "1." "2." "3." ...
                    episode_num = episode_num.replace(".", "")
                    episode_num = int(episode_num)

                    episode_name = episode_div.select_one("div:nth-child(2)").text.strip()

                    self.log_info(f"package {release_name}: episode {episode_num} {episode_name}")

                    # loop hosters
                    done_head = False
                    for hoster_link in episode_div.select("div.row > a"):
                        """
                        if not done_head:
                            self.log_info(f"package {release_name}: episode {episode_num} {episode_name}")
                            done_head = True
                        """
                        short_hoster_name = hoster_link.select_one("div > span").text.strip()
                        # TODO translate short_hoster_name to hoster_name
                        hoster_url = "https://" + self.pyfile_netloc + hoster_link["href"]
                        hoster_url = self._resolve_hoster_url(release_name, hoster_url)
                        if not hoster_url:
                            continue
                        self.log_info(f"package {release_name}: hoster {short_hoster_name} {hoster_url}")
                        release_urls.append((short_hoster_name, hoster_url))

            release_size = None # ?
            self._add_release_urls(release_name, release_size, release_urls)
            release_urls = []



    def _add_release_urls(self, release_name, release_size, release_urls):
        if not release_urls:
            return
        package_name = release_name
        if release_size:
            package_name += f" [{release_size}]"
        # TODO also add release_languages
        split_packages_by_hoster = self.config.get("split_packages_by_hoster")
        if split_packages_by_hoster:
            for hoster_name, hoster_url in release_urls:
                _package_name = package_name + f" [{hoster_name}]"
                self.packages += [
                    (_package_name, [hoster_url], _package_name)
                ]
        else:
            release_urls = list(map(lambda x: x[1], release_urls))
            self.packages += [
                (package_name, release_urls, package_name)
            ]



    def _resolve_hoster_url(self, release_name, hoster_url):

        # FIXME use some global rate-limiting
        # to allow decoding multiple serienfans.org urls in parallel
        # avoid rate-limiting (response status 429)
        time.sleep(3)

        #self.log_debug(f"package {release_name}: getting response headers from {hoster_url}")

        # retry loop
        retry_max = 10
        retry_step = 0
        while True:
            retry_step += 1
            try:
                #response = requests.head(hoster_url) # , **requests_get_kwargs)
                response_headers = self.load(hoster_url, just_header=True, redirect=False)
                break
            except BadHeader as exc:
                # Bad server response: 400 Bad Request
                if retry_step == retry_max:
                    raise
                # else: retry
                self.log_debug(f"package {release_name}: got BadHeader: {exc} -> retrying")
                time.sleep(3)

        # if response.status_code != 302:
        #     # status_code can be 429 = too many requests
        #     self.log_info(f"package {release_name}: response.status_code", response.status_code)

        # assert response.status_code == 302

        # self.log_debug(f"response_headers {json.dumps(response_headers, indent=2)}")

        # hoster_url_2 = response.headers['Location']
        hoster_url_2 = response_headers.get('location')

        if not hoster_url_2:
            self.log_error(f"got no redirect from {hoster_url}")
            return

        #self.log_info(f"package {release_name}: redirect {hoster_url} -> {hoster_url_2}")
        hoster_url = hoster_url_2
        return hoster_url



if __name__ == "__main__":
    # debug
    """
    examples:
    python src/pyload/plugins/decrypters/SerienfansOrg.py https://serienfans.org/south-park
    python src/pyload/plugins/decrypters/SerienfansOrg.py https://filmfans.org/parasite
    """

    # TODO move this to some util.py
    def mock_decrypter(cls):
        import logging
        from pyload.core.managers.file_manager import FileManager
        from pyload.core.network.request_factory import RequestFactory
        #from pyload.core.network.request_factory import get_request
        pyload_config = {
            "general": {
                "ssl_verify": False, # Verify SSL certificates
            },
            "download": {
                "ipv6": True, # allow ipv6
                "interface": "", # Download interface to bind (IP Address)
                "limit_speed": None,
            },
            "proxy": {
                "enabled": False,
            },
        }
        class MockConfig:
            # def get_plugin(self, plugin, key):
            #     print("MockConfig.get_plugin", plugin, key)
            #     return None
            def get(self, scope, key):
                try:
                    return pyload_config[scope][key]
                except KeyError:
                    pass
                print("MockConfig.get", scope, key)
                return None
        class MockPyload:
            log = logging.getLogger(__name__)
            #debug = 1 # compact debug log
            debug = 2 # trace debug log
            config = MockConfig()
            tempdir = "/tmp/pyLoad" # pyload.tempdir
            def __init__(self):
                self.log.setLevel(logging.DEBUG)
                self.files = self.file_manager = FileManager(self)
                self.req = self.request_factory = RequestFactory(self)
            def _(self, *a, **k):
                # translator function?
                return a[0]
        mock_pyload = MockPyload()
        class MockPackage:
            password = None
        import pycurl
        class MockPyFile:
            url = "http://localhost:99999999/"
            id = 123
            # set status for check_status in pyload/plugins/base/hoster.py
            # pyload.core.datatypes.enums.DownloadStatus.STARTING = 7
            status = 7
            abort = False
            _ = mock_pyload._
            def __init__(
                # actually "manager" is pyload.files
                # self.files = self.file_manager = FileManager(self)
                # self, manager, id, url, name, size, status, error, pluginname, package, order
                self, *args, **kwargs
            ):
                if args:
                    print("MockPyFile.__init__: args", args, kwargs)
                    manager, id, url, name, size, status, error, pluginname, package, order = args
                    self.id = id
                    self.url = url
                    self.name = name
                    self.size = size
                    self.status = status
                #self.m = self.manager = pycurl.CurlMulti() # no! this is FileManager
                #self.m = self.manager = manager
                self.m = self.manager = mock_pyload.files
                self._package = MockPackage()
            def package(self):
                return self._package
        def mock_init(self, *a, **k):
            mock_pyfile = MockPyFile()
            mock_pyload = MockPyload()
            self.pyload = mock_pyload
            self.pyfile = mock_pyfile
            self.config = dict()
            for config_item in self.__config__:
                key, _type, desc, default = config_item
                self.config[key] = default
            self.log_debug = lambda *a: print("debug:", *a)
            self.log_info = lambda *a: print("info:", *a)
            self.log_warning = lambda *a: print("warning:", *a)
            self.log_error = lambda *a: print("error:", *a)
        #cls.__init__ = mock_init
        pyfile = MockPyFile()
        decrypter = cls(pyfile)
        decrypter.log_debug = lambda *a: print("debug:", *a)
        decrypter.log_info = lambda *a: print("info:", *a)
        decrypter.log_warning = lambda *a: print("warning:", *a)
        decrypter.log_error = lambda *a: print("error:", *a)
        decrypter.config = dict()
        for config_item in decrypter.__config__:
            key, _type, desc, default = config_item
            decrypter.config[key] = default
        return decrypter

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    args = parser.parse_args()

    decrypter = mock_decrypter(SerienfansOrg)

    # write cache files
    decrypter._write_cache = True
    # read cache files
    decrypter._read_cache = True

    pyfile = decrypter.pyfile
    pyfile.url = args.url

    decrypter.decrypt(pyfile)

    print("decrypter.packages", decrypter.packages)
