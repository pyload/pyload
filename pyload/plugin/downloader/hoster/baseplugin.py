# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import range
from urllib.parse import urlparse
from re import match, search
from urllib.parse import unquote

from pyload.plugin.request import ResponseException
from pyload.plugin.hoster import Hoster
from pyload.utils import html_unescape, remove_chars


class BasePlugin(Hoster):
    __name__ = "BasePlugin"
    __type__ = "hoster"
    __pattern__ = r'^unmatchable$'
    __version__ = "0.19"
    __description__ = """Base Plugin when any other didnt fit"""
    __author_name__ = "RaNaN"
    __author_mail__ = "Mast3rRaNaN@hotmail.de"

    def setup(self):
        self.chunk_limit = -1
        self.resume_download = True

    def process(self, pyfile):
        """
        Main function.
        """

        #debug part, for api exerciser
        if pyfile.url.startswith("DEBUG_API"):
            self.multi_dl = False
            return

        # self.__name__ = "NetloadIn"
        # pyfile.name = "test"
        # self.html = self.load("http://localhost:9000/short")
        # self.download("http://localhost:9000/short")
        # self.api = self.load("http://localhost:9000/short")
        # self.decrypt_captcha("http://localhost:9000/captcha")
        #
        # if pyfile.url == "79":
        #     self.pyload.api.add_package("test", [str(i) for i in range(80)], 1)
        #
        # return
        if pyfile.url.startswith("http"):

            try:
                self.download_file(pyfile)
            except ResponseException as e:
                if e.code in (401, 403):
                    self.log_debug("Auth required")

                    account = self.pyload.acm.get_account_plugin('Http')
                    servers = [x['login'] for x in account.get_all_accounts()]
                    server = urlparse(pyfile.url).netloc

                    if server in servers:
                        self.log_debug("Logging on to {}".format(server))
                        self.req.add_auth(account.accounts[server]['password'])
                    else:
                        for pwd in pyfile.package().password.splitlines():
                            if ":" in pwd:
                                self.req.add_auth(pwd.strip())
                                break
                        else:
                            self.fail(_("Authorization required (username:password)"))

                    self.download_file(pyfile)
                else:
                    raise

        else:
            self.fail(_("No Plugin matched and not a downloadable url"))

    def download_file(self, pyfile):
        url = pyfile.url

        for _ in range(5):
            header = self.load(url, just_header=True)

            # self.load does not raise a BadHeader on 404 responses, do it here
            if 'code' in header and header['code'] == 404:
                raise ResponseException(404)

            if 'location' in header:
                self.log_debug("Location: {}".format(header['location']))
                base = match(r'https?://[^/]+', url).group(0)
                if header['location'].startswith("http"):
                    url = unquote(header['location'])
                elif header['location'].startswith("/"):
                    url = base + unquote(header['location'])
                else:
                    url = '{}/{}'.format(base, unquote(header['location']))
            else:
                break

        name = html_unescape(unquote(urlparse(url).path.split("/")[-1]))

        if 'content-disposition' in header:
            self.log_debug("Content-Disposition: {}".format(header['content-disposition']))
            m = search("filename(?P<type>=|\*=(?P<enc>.+)'')(?P<name>.*)", header['content-disposition'])
            if m:
                disp = m.groupdict()
                self.log_debug(disp)
                if not disp['enc']:
                    disp['enc'] = 'utf-8'
                name = remove_chars(disp['name'], "\"';").strip()
                name = str(unquote(name), disp['enc'])

        if not name:
            name = url
        pyfile.name = name
        self.log_debug("Filename: {}".format(pyfile.name))
        self.download(url, disposition=True)
