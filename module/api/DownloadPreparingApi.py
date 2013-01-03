#!/usr/bin/env python
# -*- coding: utf-8 -*-

from itertools import chain

from module.Api import Api, RequirePerm, Permission, OnlineCheck, LinkStatus, urlmatcher
from module.utils.fs import join
from module.network.RequestFactory import getURL
from module.common.packagetools import parseNames

from ApiComponent import ApiComponent

class DownloadPreparingApi(ApiComponent):
    """ All kind of methods to parse links or retrieve online status """

    @RequirePerm(Permission.Add)
    def parseURLs(self, html=None, url=None):
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

        # remove duplicates
        return self.checkURLs(set(urls))


    @RequirePerm(Permission.Add)
    def checkURLs(self, urls):
        """ Gets urls and returns pluginname mapped to list of matching urls.

        :param urls:
        :return: {plugin: urls}
        """
        data, crypter = self.core.pluginManager.parseUrls(urls)
        plugins = {}

        for url, plugin in chain(data, crypter):
            if plugin in plugins:
                plugins[plugin].append(url)
            else:
                plugins[plugin] = [url]

        return plugins

    @RequirePerm(Permission.Add)
    def checkOnlineStatus(self, urls):
        """ initiates online status check, will also decrypt files.

        :param urls:
        :return: initial set of data as :class:`OnlineCheck` instance containing the result id
        """
        data, crypter = self.core.pluginManager.parseUrls(urls)

        # initial result does not contain the crypter links
        tmp = [(url, (url, LinkStatus(url, pluginname, "unknown", 3, 0))) for url, pluginname in data]
        data = parseNames(tmp)
        result = {}

        for k, v in data.iteritems():
            for url, status in v:
                status.packagename = k
                result[url] = status

        data.update(crypter) # hoster and crypter will be processed
        rid = self.core.threadManager.createResultThread(data, False)

        return OnlineCheck(rid, result)

    @RequirePerm(Permission.Add)
    def checkOnlineStatusContainer(self, urls, container, data):
        """ checks online status of urls and a submitted container file

        :param urls: list of urls
        :param container: container file name
        :param data: file content
        :return: :class:`OnlineCheck`
        """
        th = open(join(self.core.config["general"]["download_folder"], "tmp_" + container), "wb")
        th.write(str(data))
        th.close()
        urls.append(th.name)
        return self.checkOnlineStatus(urls)

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