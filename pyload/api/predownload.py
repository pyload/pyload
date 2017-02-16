# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import io
import os
from builtins import str
from itertools import chain

from future import standard_library

from pyload.api import DownloadStatus as DS
from pyload.api import (Api, LinkStatus, OnlineCheck, Permission, require_perm,
                        urlmatcher)
from pyload.api.base import BaseApi
from pyload.network.request import get_url
from pyload.utils.packagetools import parse_names
from pyload.utils.purge import uniqify

standard_library.install_aliases()


class PreDownloadApi(BaseApi):
    """
    All kind of methods to parse links or retrieve online status.
    """

    @require_perm(Permission.Add)
    def parse_links(self, links):
        """
        Gets urls and returns pluginname mapped to list of matching urls.

        :param links:
        :return: {plugin: urls}
        """
        data, crypter = self.pyload.pgm.parse_urls(links)
        plugins = {}

        for url, plugin in chain(data, crypter):
            if plugin in plugins:
                plugins[plugin].append(url)
            else:
                plugins[plugin] = [url]

        return plugins

    @require_perm(Permission.Add)
    def check_links(self, links):
        """
        Initiates online status check, will also decrypt files.

        :param links:
        :return: initial set of data as :class:`OnlineCheck` instance containing the result id
        """
        hoster, crypter = self.pyload.pgm.parse_urls(links)

        # TODO: withhold crypter, derypt or add later
        # initial result does not contain the crypter links
        tmp = [(url, LinkStatus(url, url, -1, DS.Queued, pluginname))
               for url, pluginname in hoster]
        data = parse_names(tmp)
        rid = self.pyload.thm.create_result_thread(
            self.primary_uid, hoster + crypter)

        return OnlineCheck(rid, data)

    @require_perm(Permission.Add)
    def check_container(self, filename, data):
        """
        Checks online status of urls and a submitted container file

        :param filename: name of the file
        :param data: file content
        :return: :class:`OnlineCheck`
        """
        file = os.path.join(self.pyload.config.get(
            'general', 'storage_folder'), "tmp_{}".format(filename))
        with io.open(file, "wb") as f:
            f.write(str(data))
            return self.check_links([f.name])

    @require_perm(Permission.Add)
    def check_html(self, html, url):
        """
        Parses html content or any arbitrary text for links and returns result of `check_urls`

        :param html: html source
        :return:
        """
        urls = []
        if html:
            urls += [x[0] for x in urlmatcher.findall(html)]
        if url:
            page = get_url(url)
            urls += [x[0] for x in urlmatcher.findall(page)]

        return self.check_links(uniqify(urls))

    @require_perm(Permission.Add)
    def poll_results(self, rid):
        """
        Polls the result available for ResultID

        :param rid: `ResultID`
        :return: `OnlineCheck`, if rid is -1 then there is no more data available
        """
        result = self.pyload.thm.get_info_result(rid)
        if result and result.owner == self.primary_uid:
            return result.to_api_data()

    @require_perm(Permission.Add)
    def generate_packages(self, links):
        """
        Parses links, generates packages names from urls

        :param links: list of urls
        :return: package names mapped to urls
        """
        result = parse_names((x, x) for x in links)
        return result


if Api.extend(PreDownloadApi):
    del PreDownloadApi
