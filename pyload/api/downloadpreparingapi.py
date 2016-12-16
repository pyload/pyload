# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import unicode_literals
from builtins import str
from itertools import chain

from pyload.Api import Api, DownloadStatus as DS,\
    require_perm, Permission, OnlineCheck, LinkStatus, urlmatcher
from pyload.utils import uniqify
from pyload.utils.fs import join
from pyload.utils.packagetools import parseNames
from pyload.network.requestfactory import get_url

from .apicomponent import ApiComponent


class DownloadPreparingApi(ApiComponent):
    """ All kind of methods to parse links or retrieve online status """

    @require_perm(Permission.Add)
    def parse_links(self, links):
        """ Gets urls and returns pluginname mapped to list of matching urls.

        :param links:
        :return: {plugin: urls}
        """
        data, crypter = self.pyload.pluginManager.parseUrls(links)
        plugins = {}

        for url, plugin in chain(data, crypter):
            if plugin in plugins:
                plugins[plugin].append(url)
            else:
                plugins[plugin] = [url]

        return plugins

    @require_perm(Permission.Add)
    def check_links(self, links):
        """ initiates online status check, will also decrypt files.

        :param links:
        :return: initial set of data as :class:`OnlineCheck` instance containing the result id
        """
        hoster, crypter = self.pyload.pluginManager.parseUrls(links)

        #: TODO: withhold crypter, derypt or add later
        # initial result does not contain the crypter links
        tmp = [(url, LinkStatus(url, url, -1, DS.Queued, pluginname)) for url, pluginname in hoster]
        data = parseNames(tmp)
        rid = self.pyload.threadManager.createResultThread(self.primary_uid, hoster + crypter)

        return OnlineCheck(rid, data)

    @require_perm(Permission.Add)
    def check_container(self, filename, data):
        """ checks online status of urls and a submitted container file

        :param filename: name of the file
        :param data: file content
        :return: :class:`OnlineCheck`
        """
        th = open(join(self.pyload.config["general"]["download_folder"], "tmp_" + filename), "wb")
        th.write(str(data))
        th.close()
        return self.checkLinks([th.name])

    @require_perm(Permission.Add)
    def check_html(self, html, url):
        """Parses html content or any arbitrary text for links and returns result of `checkURLs`

        :param html: html source
        :return:
        """
        urls = []
        if html:
            urls += [x[0] for x in urlmatcher.findall(html)]
        if url:
            page = get_url(url)
            urls += [x[0] for x in urlmatcher.findall(page)]

        return self.checkLinks(uniqify(urls))

    @require_perm(Permission.Add)
    def poll_results(self, rid):
        """ Polls the result available for ResultID

        :param rid: `ResultID`
        :return: `OnlineCheck`, if rid is -1 then there is no more data available
        """
        result = self.pyload.threadManager.getInfoResult(rid)
        if result and result.owner == self.primary_uid:
            return result.toApiData()

    @require_perm(Permission.Add)
    def generate_packages(self, links):
        """ Parses links, generates packages names from urls

        :param links: list of urls
        :return: package names mapped to urls
        """
        result = parseNames((x, x) for x in links)
        return result


if Api.extend(DownloadPreparingApi):
    del DownloadPreparingApi
