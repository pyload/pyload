# -*- coding: utf-8 -*-

#
# Test links:
#   https://serienfans.org/breaking-bad

import base64
import re
import urllib.parse
import time
import json

from bs4 import BeautifulSoup

from pyload.core.network.http.http_request import HTTPRequest

from ..base.decrypter import BaseDecrypter


class SerienfansOrg(BaseDecrypter):
    __name__ = "SerienfansOrg"
    __type__ = "decrypter"
    __version__ = "0.1"
    __status__ = "testing"


    __pattern__ = r"https?://(?:www\.)?(?:serienfans|filmfans)\.org/[\w-]+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("prefer_video_quality", "0;180p;240p;360p;480p;720p;1080p;2160p", "Prefer video quality", "720p"),
        ("use_first_online_hoster_only", "bool", "Use first online hoster only", True),
        # TODO implement ...
        # ("randomize_online_hosters", "bool", "Randomize online hosters", True),
        # ("prefer_hosters", "bool", "Prefer hosters", False),
        # ("prefer_hosters_list", "str", "Prefer hosters list", "rapidgator 1fichier katfile turbobit"),
        # ("include_episode_links", "bool", "Include episode links", False),
    ]

    __description__ = """Serienfans.org decrypter plugin"""
    __license__ = "MIT"
    __authors__ = [
        ("milahu", "milahu@gmail.com"),
    ]

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

        # why should we set self.data?
        # self.data = self.load(pyfile.url)

        # usually this is "serienfans.org" or "filmfans.org"
        pyfile_netloc = urllib.parse.urlparse(pyfile.url).netloc.lower()

        # fix: FilecryptCc: Folder is password protected
        self.log_debug(f"setting password: {pyfile_netloc}")
        self.pyfile.package().password = pyfile_netloc

        html = self.load(pyfile.url)

        # TODO check for http status 404
        if self.data == "Not Found":
            self.offline()
            return

        init_season_match = re.search(r"initSeason\('([0-9a-zA-Z]+)', ([0-9]+), '', 'ALL'\);", html)

        # random string
        session_id = init_season_match.group(1)

        # example: 5
        num_seasons = int(init_season_match.group(2))

        # list of known release qualities
        release_quality_list = next(c for c in self.__config__ if c[0] == "prefer_video_quality")[1].split(";")[1:]
        # self.log_debug(f"release_quality_list {release_quality_list}")

        prefer_video_quality = self.config.get("prefer_video_quality")

        use_first_online_hoster_only = self.config.get("use_first_online_hoster_only")

        self.packages = []

        # loop seasons
        for season_num in range(1, 1 + num_seasons):

            # FIXME use some global rate-limiting
            # to allow decoding multiple serienfans.org urls in parallel
            # sleep between requests to avoid rate-limiting
            time.sleep(1)

            request_time = int(time.time() * 1000)
            season_url = f"https://{pyfile_netloc}/api/v1/{session_id}/season/{season_num}?_={request_time}"

            season_text = self.load(season_url)
            season = json.loads(season_text)

            # season["qualitys"] # ["1080p", "480p", "720p"]
            # TODO filter by quality
            #   but only as a secondary filter after the season + episode filter

            # season["bubblesQuality"] # ?

            # season["languages"] # ["DE", "EN"]
            # TODO filter by language
            #   but only as a secondary filter after the season + episode filter

            # season["bubblesLanguage"] # ?

            season_html = season["html"]

            season_soup = BeautifulSoup(season_html, "html.parser")

            for entry in season_soup.select("div.entry"):

                # entry: div.row, div.row, div.list.simple
                release_name = entry.select_one("small").text.strip()
                self.log_info(f"package {release_name}")

                # example: "480p | 1.3 GB"
                release_morespec = entry.select_one("div:nth-child(1) > div > h3 > span.morespec").text.strip()

                release_quality = release_morespec.split(" | ")[0].lower()
                if not release_quality in release_quality_list:
                    release_quality = None

                if (
                    release_quality and
                    prefer_video_quality != "0" and
                    release_quality != prefer_video_quality
                ):
                    self.log_debug(f"package {release_name}: skipping quality {release_quality} != {prefer_video_quality}")
                    continue
                    # TODO use other quality if the preferred quality is not available
                    # first try better quality, then worse quality

                # example: "4SF"
                # release_grouptag = entry.select_one("div:nth-child(1) > div > h3 > span.grouptag").text.strip()

                # loop hosters: complete seasons

                release_urls = []

                for hoster_link in entry.select("div:nth-child(2) > a"):

                    # skip offline links
                    link_online = True
                    if hoster_link.select_one("i.st.off"):
                        link_online = False
                    elif hoster_link.select_one("i.st.mix"):
                        # status: mixed
                        # only some links are online
                        link_online = None
                    #elif hoster_link.select_one("i.st"):
                    #    link_online = True

                    if link_online == False:
                        # skip offline link
                        continue

                    link_status = "online" if link_online else "mixed"

                    hoster_name = hoster_link.select_one("div > span").text.strip()
                    # hoster_url returns redirect to filecrypt.co (etc)
                    # hoster_url expires after some time

                    if use_first_online_hoster_only and link_online == None:
                        # skip mixed link
                        self.log_debug(f"package {release_name}: skipping mixed-online hoster: {hoster_name}")
                        continue

                    hoster_url = "https://" + pyfile_netloc + hoster_link["href"]

                    # FIXME use some global rate-limiting
                    # to allow decoding multiple serienfans.org urls in parallel
                    # avoid rate-limiting (response status 429)
                    time.sleep(3)

                    #response = requests.head(hoster_url) # , **requests_get_kwargs)
                    response_headers = self.load(hoster_url, just_header=True, redirect=False)

                    # if response.status_code != 302:
                    #     # status_code can be 429 = too many requests
                    #     self.log_info(f"package {release_name}: response.status_code", response.status_code)

                    # assert response.status_code == 302

                    # self.log_debug(f"response_headers {json.dumps(response_headers, indent=2)}")

                    # hoster_url_2 = response.headers['Location']
                    hoster_url_2 = response_headers.get('location')

                    if not hoster_url_2:
                        self.log_error(f"got no redirect from {hoster_url}")
                        continue

                    #self.log_info(f"package {release_name}: redirect {hoster_url} -> {hoster_url_2}")
                    hoster_url = hoster_url_2
                    self.log_info(f"package {release_name}: hoster {hoster_name} {link_status} {hoster_url}")

                    release_urls.append(hoster_url)

                    # TODO group hoster_url by container ID
                    # example
                    # hoster 1fichier   https://filecrypt.cc/Container/6e6eb65ace.html?mirror=0
                    # hoster rapidgator https://filecrypt.cc/Container/6e6eb65ace.html?mirror=1
                    # hoster ddownload  https://filecrypt.cc/Container/6e6eb65ace.html?mirror=2
                    # hoster katfile    https://filecrypt.cc/Container/6e6eb65ace.html?mirror=3

                    # break # debug: stop after first hoster_link

                    if use_first_online_hoster_only and link_online == True:
                        # stop after first online link
                        self.log_debug(f"package {release_name}: using first online hoster only: {hoster_name}")
                        break

                if release_urls:

                    self.packages += [
                        (release_name, release_urls, release_name)
                    ]



                # TODO remove?

                include_episode_links = False

                if include_episode_links:

                    # loop hosters: episodes
                    # NOTE most download links are complete seasons

                    # body > div:nth-child(6) > div.list.simple > div:nth-child(2) > div:nth-child(2)
                    # body > div:nth-child(6) > div.list.simple > div:nth-child(3) > div:nth-child(2)
                    # body > div:nth-child(6) > div.list.simple > div:nth-child(4) > div:nth-child(2)

                    for episode_div in entry.select("div.list.simple > div.row:not(.head)"):
                    #for episode_div in entry.select("div.list.simple > div.row"):

                        # body > div:nth-child(2) > div.list.simple > div:nth-child(2) > div:nth-child(1)
                        # body > div:nth-child(2) > div.list.simple > div:nth-child(3) > div:nth-child(1)
                        # body > div:nth-child(2) > div.list.simple > div:nth-child(4) > div:nth-child(1)
                        episode_num = episode_div.select_one("div:nth-child(1)").text.strip() # "1." "2." "3." ...
                        episode_num = episode_num.replace(".", "")
                        episode_num = int(episode_num)

                        # body > div:nth-child(2) > div.list.simple > div:nth-child(2) > div:nth-child(2)
                        # body > div:nth-child(2) > div.list.simple > div:nth-child(3) > div:nth-child(2)
                        # body > div:nth-child(2) > div.list.simple > div:nth-child(4) > div:nth-child(2)
                        episode_name = episode_div.select_one("div:nth-child(2)").text.strip()

                        self.log_info(f"package {release_name}: episode {episode_num} {episode_name}")

                        # for episode_div in entry.select("div.list.simple > div.row"):

                        # loop hosters

                        # body > div:nth-child(2) > div.list.simple > div:nth-child(2) > div.row > a:nth-child(1) > div > span
                        # body > div:nth-child(2) > div.list.simple > div:nth-child(2) > div.row > a:nth-child(2) > div > span
                        #        entry                                episode_div                  hoster_link

                        # body > div:nth-child(2) > div.list.simple > div:nth-child(3) > div.row > a:nth-child(1) > div > span
                        # body > div:nth-child(2) > div.list.simple > div:nth-child(3) > div.row > a:nth-child(2) > div > span
                        #        entry                                episode_div                  hoster_link

                        done_head = False

                        #for hoster_link in episode_div.select("div:nth-child(2) > div.row > a"):
                        for hoster_link in episode_div.select("div.row > a"):
                            """
                            if not done_head:
                                self.log_info(f"package {release_name}: episode {episode_num} {episode_name}")
                                done_head = True
                            """
                            short_hoster_name = hoster_link.select_one("div > span").text.strip()
                            hoster_url = "https://" + pyfile_netloc + hoster_link["href"]
                            self.log_info(f"package {release_name}: hoster {short_hoster_name} {hoster_url}")

            # break # debug: stop after first season
