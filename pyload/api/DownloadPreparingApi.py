#!/usr/bin/env python
# -*- coding: utf-8 -*-

from itertools import chain

from pyload.Api import Api, DownloadStatus as DS,\
    RequirePerm, Permission, OnlineCheck, LinkStatus, urlmatcher
from pyload.utils import uniqify
from pyload.utils.fs import join
from pyload.utils.packagetools import parseNames
from pyload.network.RequestFactory import getURL

from ApiComponent import ApiComponent

class DownloadPreparingApi(ApiComponent):
    """ All kind of methods to parse links or retrieve online status """

    @RequirePerm(Permission.Add)
    def parseLinks(self, links):
        """ Gets urls and returns pluginname mapped to list of matching urls.

        :param links:
        :return: {plugin: urls}
        """
        data, crypter = self.core.pluginManager.parseUrls(links)
        plugins = {}

        for url, plugin in chain(data, crypter):
            if plugin in plugins:
                plugins[plugin].append(url)
            else:
                plugins[plugin] = [url]

        return plugins

    @RequirePerm(Permission.Add)
    def checkLinks(self, links):
        """ initiates online status check, will also decrypt files.

        :param urls:
        :return: initial set of data as :class:`OnlineCheck` instance containing the result id
        """
        hoster, crypter = self.core.pluginManager.parseUrls(links)

        #: TODO: withhold crypter, derypt or add later
        # initial result does not contain the crypter links
        tmp = [(url, LinkStatus(url, url, pluginname, -1, DS.Queued)) for url, pluginname in hoster + crypter]
        data = parseNames(tmp)
        rid = self.core.threadManager.createResultThread(data)

        return OnlineCheck(rid, data)

    @RequirePerm(Permission.Add)
    def checkContainer(self, filename, data):
        """ checks online status of urls and a submitted container file

        :param urls: list of urls
        :param container: container file name
        :param data: file content
        :return: :class:`OnlineCheck`
        """
        th = open(join(self.config["general"]["download_folder"], "tmp_" + filename), "wb")
        th.write(str(data))
        th.close()
        return self.checkLinks([th.name])

    @RequirePerm(Permission.Add)
    def checkHTML(self, html, url):
        """Parses html content or any arbitrary text for links and returns result of `checkURLs`

        :param html: html source
        :return:
        """
        urls = []
        if html:
            urls += [x[0] for x in urlmatcher.findall(html)]
        if url:
            page = getURL(url)
            urls += [x[0] for x in urlmatcher.findall(page)]

        return self.checkLinks(uniqify(urls))

    @RequirePerm(Permission.Add)
    def pollResults(self, rid):
        """ Polls the result available for ResultID

        :param rid: `ResultID`
        :return: `OnlineCheck`, if rid is -1 then there is no more data available
        """
        result = self.core.threadManager.getInfoResult(rid)

        if "ALL_INFO_FETCHED" in result:
            del result["ALL_INFO_FETCHED"]
            return OnlineCheck(-1, result)
        else:
            return OnlineCheck(rid, result)


    @RequirePerm(Permission.Add)
    def generatePackages(self, links):
        """ Parses links, generates packages names from urls

        :param links: list of urls
        :return: package names mapped to urls
        """
        result = parseNames((x, x) for x in links)
        return result


if Api.extend(DownloadPreparingApi):
    del DownloadPreparingApi