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
import functools

from bs4 import BeautifulSoup

if __name__ == "__main__":
    import os
    import sys
    # fix: ModuleNotFoundError: No module named 'pyload'
    sys.path.insert(0, os.path.dirname(__file__) + "/../../..")

from pyload.core.network.http.http_request import HTTPRequest
from pyload.plugins.base.decrypter import BaseDecrypter
from pyload.core.network.http.exceptions import BadHeader


class Release:
    name = None
    quality = None
    size = None
    urls = []
    entry = None


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
        ("prefer_video_quality", "none;180p;240p;360p;480p;720p;1080p;1440p;2160p;4320p", "Prefer video quality", "1080p"),
        ("max_video_quality", "none;180p;240p;360p;480p;720p;1080p;1440p;2160p;4320p", "Maximum video quality", "1080p"),
        ("min_video_quality", "none;180p;240p;360p;480p;720p;1080p;1440p;2160p;4320p", "Minimum video quality", "720p"),
        # TODO dont trust online status reported by serienfans
        ("use_first_online_hoster_only", "bool", "Use first online hoster only", False),
        # TODO implement ...
        # ("randomize_online_hosters", "bool", "Randomize online hosters", True),
        ("prefer_hoster", "none;rapidgator;1fichier;katfile;turbobit;ddownload", "Prefer hoster", "rapidgator"),
        # ("prefer_hosters", "bool", "Prefer hosters", False),
        # ("prefer_hosters_list", "str", "Prefer hosters list", "rapidgator 1fichier katfile turbobit"),
        ("include_episode_links", "bool", "Include episode links", False),
        # FIXME with split == False, pyload should merge packages with same name but different hosters
        # FIXME in any case, pyload should deduplicate download links per file -> download the same file only once
        ("split_packages_by_hoster", "bool", "Split packages by hoster", True),
    ]

    __description__ = """Serienfans.org decrypter plugin"""
    __license__ = "MIT"
    __authors__ = [
        ("milahu", "milahu@gmail.com"),
    ]

    # short names are used for single-episode links at serienfans.org
    _hoster_name_map = {
        "1F": "1fichier",
        "RG": "rapidgator",
        "DD": "ddownload",
        # TODO more
        # "??": "katfile",
        # "??": "turbobit",
        # "??": "frdl",
    }

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

        self.pyfile_url_parsed = urllib.parse.urlparse(pyfile.url)

        # usually this is "serienfans.org" or "filmfans.org"
        self.pyfile_netloc = self.pyfile_url_parsed.netloc.lower()
        if self.pyfile_netloc.startswith("www."):
            self.pyfile_netloc = self.pyfile_netloc[4:]

        # parse query string in url fragment
        # example: s=25 -> only fetch season 25
        self.pyfile_fragment = urllib.parse.parse_qs(self.pyfile_url_parsed.fragment)

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

        self._decrypt_configure()

        self._decrypt_run()

    def _decrypt_configure(self):

        # list of known release qualities
        self.release_quality_list = next(c for c in self.__config__ if c[0] == "prefer_video_quality")[1].split(";")[1:]
        # self.log_debug(f"self.release_quality_list {self.release_quality_list}")

        self.prefer_video_quality = self.config.get("prefer_video_quality")
        self.prefer_hoster = self.config.get("prefer_hoster")
        self.max_video_quality = self.config.get("max_video_quality")
        self.min_video_quality = self.config.get("min_video_quality")
        self.use_first_online_hoster_only = self.config.get("use_first_online_hoster_only")
        self.include_episode_links = self.config.get("include_episode_links")
        self.include_season_links = True

        # "none" -> None
        self.log_info(f"self.config {self.config}")
        for key in self.config.keys():
            if hasattr(self, key) and getattr(self, key) == "none":
                setattr(self, key, None)

        # quality
        if q := self.pyfile_fragment.get("q"):
            self.prefer_video_quality = q[0]
            self.log_info(f"quality: {self.prefer_video_quality}")

        # season
        if s := self.pyfile_fragment.get("s"):
            self.season_num_list = list(map(int, re.findall("[0-9]+", " ".join(s))))
            self.log_info(f"seasons: {self.season_num_list}")
        else:
            # fetch all seasons
            self.season_num_list = range(1, 1 + self.num_seasons)

        # episode
        if e := self.pyfile_fragment.get("e"):
            self.episode_num_list = list(map(int, re.findall("[0-9]+", " ".join(e))))
            self.include_episode_links = True
            self.include_season_links = False
            self.log_info(f"episodes: {self.episode_num_list}")
        else:
            # fetch all episodes
            self.episode_num_list = None

    def _decrypt_run(self):

        for season_num in self.season_num_list:
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

        #self.log_info(f"response_2_json {repr(response_2_json)[:1000]} ...")

        # response_2_json["qualitys"] # ["1080p", "480p", "720p"]
        # TODO filter by quality
        #   but only as a secondary filter after the movie + episode filter

        # response_2_json["bubblesQuality"] # ?

        # response_2_json["languages"] # ["DE", "EN"]
        # TODO filter by language
        #   but only as a secondary filter after the movie + episode filter

        # response_2_json["bubblesLanguage"] # ?

        if response_2_json.get("error") == True:
            # usually "an error occured" (helpful...)
            # caused by
            # https://filmfans.org/shutter-island
            message = response_2_json.get("message")
            self.log_error(f"server error: {message}")
            return

        response_2_html = response_2_json.get("html")

        if response_2_html is None:
            self.log_error(f"no html in response_2_json: {json.dumps(response_2_json, indent=2)}")
            return

        html_not_found = '\n Leider liegen zu dieser Staffel noch keine Einträge vor\n '
        if response_2_html == html_not_found:
            self.log_error("empty result")
            return

        self.packages = []

        movie_soup = BeautifulSoup(response_2_html, "html.parser")

        # later: sort release_list by quality
        release_list = []

        # loop unsorted releases
        for release_entry in movie_soup.select("div.entry"):

            release = Release()
            release_list.append(release)

            release.entry = release_entry

            if self._is_serienfans:
                # release.entry: div.row, div.row, div.list.simple
                release.name = release.entry.select_one("small").text.strip()
            elif self._is_filmfans:
                release.name = release.entry.select_one("h3 > span").text.strip()

            self.log_info(f"release {release.name}")

            if self._is_serienfans:
                # example: "480p | 1.3 GB"
                release_morespec = release.entry.select_one("div:nth-child(1) > div > h3 > span.morespec").text.strip()
                morespec_list = release_morespec.split(" | ")
                if len(morespec_list) >= 1:
                    release.quality = morespec_list[0].lower()
                if len(morespec_list) >= 2:
                    release.size = morespec_list[1]
                # release_audio = ?
                # example: "4SF"
                # release_grouptag = release.entry.select_one("div:nth-child(1) > div > h3 > span.grouptag").text.strip()
            elif self._is_filmfans:
                # parse key-value pairs
                release_info = dict()
                for audiotag in release.entry.select("span.audiotag"):
                    key = audiotag.select_one("small").text.strip()
                    if key[-1] == ":":
                        key = key[:-1]
                    # key = translate_key.get(key, key)
                    # print("audiotag.contents", audiotag.contents)
                    val = audiotag.contents[2].text.strip()
                    release_info[key] = val
                # self.log_debug(f"package {release.name}: release_info {release_info}")
                release.quality = release_info.get("Auflösung")
                if type(release.quality) == str:
                    release.quality = release.quality.lower()
                release.size = release_info.get("Größe")
                # release_audio = release_info.get("Audio")
                # release_grouptag = release_info.get("Releasegruppe")

            if not release.quality in self.release_quality_list:
                release.quality = None

        if self.prefer_video_quality != None:
            # sort release_list by quality
            def compare_release_quality(a, b):
                return compare_quality(a.quality, b.quality)
            def compare_quality(a, b):
                if a == b: return 0
                a = a.lower()
                b = b.lower()
                if a == b: return 0
                # TODO "p" or "i" = progressive or interlaced
                if a.endswith("p") and b.endswith("p"):
                    a = int(a[:-1])
                    b = int(b[:-1])
                    if a == b: return 0
                    if a < b: return -1
                    if a > b: return +1
                return -1 # a < b
            sort_key_release_quality = functools.cmp_to_key(compare_release_quality)
            def filter_same_quality(release):
                return compare_quality(release.quality, self.prefer_video_quality) == 0
            def filter_better_quality(release):
                if (
                    self.max_video_quality != None
                    and
                    compare_quality(release.quality, self.max_video_quality) == +1
                ):
                    # release.quality is better than self.max_video_quality
                    return False
                return compare_quality(release.quality, self.prefer_video_quality) == +1
            def filter_worse_quality(release):
                if (
                    self.min_video_quality != None
                    and
                    compare_quality(release.quality, self.min_video_quality) == -1
                ):
                    # release.quality is worse than self.min_video_quality
                    return False
                return (
                    release.quality == None
                    or
                    compare_quality(release.quality, self.prefer_video_quality) == -1
                )
            def same_quality(release_list):
                return filter(filter_same_quality, release_list)
            def better_quality(release_list):
                return sorted(filter(filter_better_quality, release_list), key=sort_key_release_quality)
            def worse_quality(release_list):
                return reversed(sorted(filter(filter_worse_quality, release_list), key=sort_key_release_quality))
            def format_release_list(release_list):
                result = ""
                for release in release_list:
                    # TODO use NamedTuple for release.urls
                    # no. all release.urls are empty here
                    # hosters_str = ", ".join(list(set(map(lambda x: x[0], release.urls))))
                    # result += f"\n  {release.quality}   {release.name}   size: {release.size}   hosters: {hosters_str}"
                    result += f"\n  {release.quality}   {release.name}   size: {release.size}"
                return result
            self.log_debug(f"raw release_list: {format_release_list(release_list)}")
            release_list = [
                *(same_quality(release_list)),
                *(better_quality(release_list)),
                *(worse_quality(release_list)),
            ]
            self.log_debug(f"sorted and filtered release_list: {format_release_list(release_list)}")

        # loop sorted releases
        for release in release_list:

            # TODO move down
            """
            if (
                release.quality and
                self.prefer_video_quality != None and
                release.quality != self.prefer_video_quality
            ):
                self.log_debug(f"package {release.name}: skipping quality {release.quality} != {self.prefer_video_quality}")
                continue
                # TODO use other quality if the preferred quality is not available
                # first try better quality, then worse quality
            """

            if self.include_season_links:

                # start new package
                release.urls = []

                if self._is_serienfans:
                    hoster_link_selector = "div:nth-child(2) > a"
                elif self._is_filmfans:
                    hoster_link_selector = "div:nth-child(3) > a"

                # loop hosters
                self.log_debug(f"package {release.name}: looping hosters")
                for hoster_link in release.entry.select(hoster_link_selector):

                    #self.log_debug(f"package {release.name}: hoster_link {hoster_link}")

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
                        self.log_debug(f"package {release.name}: skipping offline hoster {hoster_name}")
                        continue

                    link_status = "online" if link_online else "mixed"

                    # TODO remove. dont trust the online status
                    if self.use_first_online_hoster_only and link_online == None:
                        # skip mixed link
                        self.log_debug(f"package {release.name}: skipping mixed-online hoster: {hoster_name}")
                        continue

                    hoster_url = "https://" + self.pyfile_netloc + hoster_link["href"]
                    hoster_url = self._resolve_hoster_url(release.name, hoster_url)
                    if not hoster_url:
                        continue

                    self.log_info(f"release {release.name}: hoster {hoster_name} {link_status} {hoster_url}")
                    # TODO use NamedTuple for release.urls
                    release.urls.append((hoster_name, hoster_url))

                    # break # debug: stop after first hoster_link

                    if self.use_first_online_hoster_only and link_online == True:
                        # stop after first online link
                        self.log_debug(f"package {release.name}: using first online hoster only: {hoster_name}")
                        break

                self._add_release_urls(release)
                # start new package
                release.urls = []

            if self._is_serienfans and self.include_episode_links:

                # add episode links to separate package
                # start new package
                release.urls = []
                package_name = release.name + " [episodes]"
                release.size = None

                # loop hosters
                # NOTE most download links are complete seasons
                for episode_div in release.entry.select("div.list.simple > div.row:not(.head)"):

                    episode_num = episode_div.select_one("div:nth-child(1)").text.strip() # "1." "2." "3." ...
                    episode_num = episode_num.replace(".", "")
                    episode_num = int(episode_num)

                    if self.episode_num_list and not episode_num in self.episode_num_list:
                        continue

                    episode_name = episode_div.select_one("div:nth-child(2)").text.strip()

                    self.log_info(f"release {release.name}: episode {episode_num} {episode_name}")

                    # loop hosters
                    done_head = False
                    for hoster_link in episode_div.select("div.row > a"):
                        """
                        if not done_head:
                            self.log_info(f"release {release.name}: episode {episode_num} {episode_name}")
                            done_head = True
                        """
                        short_hoster_name = hoster_link.select_one("div > span").text.strip()
                        hoster_name = self._hoster_name_map.get(short_hoster_name)
                        if not hoster_name:
                            self.log_warning(f"using short_hoster_name as hoster_name: {short_hoster_name}. TODO add hoster_name to _hoster_name_map")
                            hoster_name = short_hoster_name
                        # TODO translate short_hoster_name to hoster_name
                        hoster_url = "https://" + self.pyfile_netloc + hoster_link["href"]
                        hoster_url = self._resolve_hoster_url(release.name, hoster_url)
                        if not hoster_url:
                            continue
                        self.log_info(f"release {release.name}: hoster {hoster_name} {hoster_url}")
                        # TODO use NamedTuple for release.urls
                        release.urls.append((hoster_name, hoster_url))

            release.size = None # ?
            self._add_release_urls(release)
            # start new package
            release.urls = []



    def _add_release_urls(self, release):
        if not release.urls:
            return
        package_name = release.name
        if release.size:
            package_name += f" [{release.size}]"
        # TODO also add release_languages to package_name
        # TODO config: use_preferred_hoster_only
        # TODO if preferred hoster was found, add other hosters in "paused" state (package collector)
        # and only add preferred hoster links to the download queue
        if self.prefer_hoster != None:
            # sort hosters. preferred hoster first
            release.urls = [
                # TODO use NamedTuple for release.urls
                *filter(lambda hu: hu[0] == self.prefer_hoster, release.urls),
                *filter(lambda hu: hu[0] != self.prefer_hoster, release.urls),
            ]
        split_packages_by_hoster = self.config.get("split_packages_by_hoster")
        if split_packages_by_hoster:
            # TODO use NamedTuple for release.urls
            for hoster_name, hoster_url in release.urls:
                _package_name = package_name + f" [{hoster_name}]"
                self.packages += [
                    (_package_name, [hoster_url], _package_name)
                ]
        else:
            # TODO use NamedTuple for release.urls
            package_urls = list(map(lambda x: x[1], release.urls))
            self.packages += [
                (package_name, package_urls, package_name)
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
        #     self.log_info(f"release {release_name}: response.status_code", response.status_code)

        # assert response.status_code == 302

        # self.log_debug(f"response_headers {json.dumps(response_headers, indent=2)}")

        # hoster_url_2 = response.headers['Location']
        hoster_url_2 = response_headers.get('location')

        if not hoster_url_2:
            self.log_error(f"got no redirect from {hoster_url}")
            return

        #self.log_info(f"release {release_name}: redirect {hoster_url} -> {hoster_url_2}")
        hoster_url = hoster_url_2
        return hoster_url


# TODO move this to some util.py
def _mock_decrypter(cls):
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


if __name__ == "__main__":
    # debug
    """
    examples:
    python src/pyload/plugins/decrypters/SerienfansOrg.py https://serienfans.org/south-park
    python src/pyload/plugins/decrypters/SerienfansOrg.py https://filmfans.org/parasite
    """

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    args = parser.parse_args()

    decrypter = _mock_decrypter(SerienfansOrg)

    # write cache files
    decrypter._write_cache = True
    # read cache files
    decrypter._read_cache = True

    pyfile = decrypter.pyfile
    pyfile.url = args.url

    decrypter.decrypt(pyfile)

    print("decrypter.packages", decrypter.packages)
