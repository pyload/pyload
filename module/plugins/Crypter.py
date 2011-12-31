# -*- coding: utf-8 -*-

from module.Api import Destination
from module.common.packagetools import parseNames
from module.utils import to_list
from module.utils.fs import exists

from Base import Base, Retry

class Package:
    """ Container that indicates new package should be created """
    def __init__(self, name, urls=None, dest=Destination.Queue):
        self.name = name,
        self.urls = urls if urls else []
        self.dest = dest

    def addUrl(self, url):
        self.urls.append(url)

class PyFileMockup:
    """ Legacy class needed by old crypter plugins """
    def __init__(self, url):
        self.url = url
        self.name = url

class Crypter(Base):
    """
    Base class for (de)crypter plugins. Overwrite decrypt* methods.

    How to use decrypt* methods
    ---------------------------

    You have to overwrite at least one method of decryptURL, decryptURLs, decryptFile.

    After decrypting and generating urls/packages you have to return the result at the\
    end of your method. Valid return Data is:

    `Package` instance
        A **new** package will be created with the name and the urls of the object.

    List of urls and `Package` instances
        All urls in the list will be added to the **current** package. For each `Package`\
        instance a new package will be created.

    """

    @classmethod
    def decrypt(cls, core, url_or_urls):
        """Static method to decrypt, something. Can be used by other plugins.

        :param core: pyLoad `Core`, needed in decrypt context
        :param url_or_urls: List of urls or urls
        :return: List of decrypted urls, all packages info removed
        """
        urls = to_list(url_or_urls)
        p = cls(core)
        try:
            result = p.processDecrypt(urls)
        finally:
            p.clean()

        ret = []

        for url_or_pack in result:
            if isinstance(url_or_pack, Package): #package
                ret.extend(url_or_pack.urls)
            else: # single url
                ret.append(url_or_pack)

        return ret

    def __init__(self, core, pid=-1, password=None):
        Base.__init__(self, core)
        self.req = core.requestFactory.getRequest(self.__name__)

        # Package id plugin was initilized for, dont use this, its not guaranteed to be set
        self.pid = pid

        #: Password supplied by user
        self.password = password

        # For old style decrypter, do not use these !
        self.packages = []
        self.urls = []
        self.pyfile = None

        self.init()

    def init(self):
        """More init stuff if needed"""

    def setup(self):
        """Called everytime before decrypting. A Crypter plugin will be most likly used for several jobs."""

    def decryptURL(self, url):
        """Decrypt a single url

        :param url: url to decrypt
        :return: See `Crypter` Documentation
        """
        raise NotImplementedError

    def decryptURLs(self, urls):
        """Decrypt a bunch of urls

        :param urls: list of urls
        :return: See `Crypter` Documentation
        """
        raise NotImplementedError

    def decryptFile(self, content):
        """Decrypt file content

        :param content: content to decrypt as string
        :return: See `Crypter Documentation
        """
        raise NotImplementedError

    def generatePackages(self, urls):
        """Generates `Package` instances and names from urls. Usefull for many different link and no\
        given package name.

        :param urls: list of urls
        :return: list of `Package`
        """
        return [Package(name, purls) for name, purls in parseNames([(url,url) for url in urls]).iteritems()]

    def processDecrypt(self, urls):
        """ Internal  method to select decrypting method

        :param urls: List of urls/content
        :return:
        """
        cls = self.__class__

        # seperate local and remote files
        content, urls = self.getLocalContent(urls)

        if hasattr(cls, "decryptURLs"):
            self.setup()
            result = to_list(self.decryptURLs(urls))
        elif hasattr(cls, "decryptURL"):
            result = []
            for url in urls:
                self.setup()
                result.extend(to_list(self.decryptURL(url)))
        elif hasattr(cls, "decrypt"):
            self.logDebug("Deprecated .decrypt() method in Crypter plugin")
            result = [] # TODO
        else:
            self.logError("No Decrypting method was overwritten")
            result = []

        if hasattr(cls, "decryptFile"):
            for c in content:
                self.setup()
                result.extend(to_list(self.decryptFile(c)))

        return result

    def getLocalContent(self, urls):
        """Load files from disk

        :param urls:
        :return: content, remote urls
        """
        content = []
        # do nothing if no decryptFile method
        if hasattr(self.__class__, "decryptFile"):
            remote = []
            for url in urls:
                path = None
                if url.startswith("http"):
                    path = None # skip directly
                elif exists(url):
                    path = url
                elif exists(self.core.path(url)):
                    path = self.core.path(url)

                if path:
                    f = open(path, "wb")
                    content.append(f.read())
                    f.close()
                else:
                    remote.append(url)

            #swap filtered url list
            urls = remote

        return content, urls

    def retry(self):
        """ Retry decrypting, will only work once. Somewhat deprecated method, should be avoided. """
        raise Retry()

    def createPackages(self):
        """ Deprecated """
        self.logDebug("Deprecated method .createPackages()")
        for pack in self.packages:

            self.log.debug("Parsed package %(name)s with %(len)d links" % { "name" : pack[0], "len" : len(pack[1]) } )
            
            links = [x.decode("utf-8") for x in pack[1]]
            
            pid = self.core.api.files.addLinks(self.pid, links)


        if self.urls:
            self.core.api.generateAndAddPackages(self.urls)
            
    def clean(self):
        if hasattr(self, "req"):
            self.req.close()
            del self.req