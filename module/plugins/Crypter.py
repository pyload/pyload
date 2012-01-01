# -*- coding: utf-8 -*-

from traceback import print_exc

from module.Api import Destination
from module.common.packagetools import parseNames
from module.utils import to_list, has_method
from module.utils.fs import exists, remove, fs_encode

from Base import Base, Retry

class Package:
    """ Container that indicates new package should be created """
    def __init__(self, name, urls=None, dest=Destination.Queue):
        self.name = name,
        self.urls = urls if urls else []
        self.dest = dest

    def addUrl(self, url):
        self.urls.append(url)

    def __eq__(self, other):
        return self.name == other.name and self.urls == other.urls

    def __repr__(self):
        return "<CrypterPackage name=%s, links=%s, dest=%s" % (self.name, self.urls, self.dest)

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
        :param url_or_urls: List of urls or single url/ file content
        :return: List of decrypted urls, all package info removed
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
        # eliminate duplicates
        return set(ret)

    def __init__(self, core, package=None, password=None):
        Base.__init__(self, core)
        self.req = core.requestFactory.getRequest(self.__name__)

        # Package the plugin was initialized for, dont use this, its not guaranteed to be set
        self.package = package
        #: Password supplied by user
        self.password = password
        #: Propose a renaming of the owner package
        self.rename = None

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

    def _decrypt(self, urls):
        """ Internal  method to select decrypting method

        :param urls: List of urls/content
        :return:
        """
        cls = self.__class__

        # seperate local and remote files
        content, urls = self.getLocalContent(urls)

        if has_method(cls, "decryptURLs"):
            self.setup()
            result = to_list(self.decryptURLs(urls))
        elif has_method(cls, "decryptURL"):
            result = []
            for url in urls:
                self.setup()
                result.extend(to_list(self.decryptURL(url)))
        elif has_method(cls, "decrypt"):
            self.logDebug("Deprecated .decrypt() method in Crypter plugin")
            self.setup()
            self.decrypt()
            result = self.convertPackages()
        else:
            if not has_method(cls, "decryptFile") or urls:
                self.logDebug("No suited decrypting method was overwritten in plugin")
            result = []

        if has_method(cls, "decryptFile"):
            for f, c in content:
                self.setup()
                result.extend(to_list(self.decryptFile(c)))
                try:
                    if f.startswith("tmp_"): remove(f)
                except :
                    pass

        return result

    def processDecrypt(self, urls):
        """ Catches all exceptions in decrypt methods and return results

        :return: Decrypting results
        """
        try:
            return self._decrypt(urls)
        except Exception:
            if self.core.debug:
                print_exc()
            return []

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
                    pass
                elif exists(url):
                    path = url
                elif exists(self.core.path(url)):
                    path = self.core.path(url)

                if path:
                    try:
                        f = open(fs_encode(path), "rb")
                        content.append((f.name, f.read()))
                        f.close()
                    except IOError, e:
                        self.logError("IOError", e)
                else:
                    remote.append(url)

            #swap filtered url list
            urls = remote

        return content, urls

    def retry(self):
        """ Retry decrypting, will only work once. Somewhat deprecated method, should be avoided. """
        raise Retry()

    def convertPackages(self):
        """ Deprecated """
        self.logDebug("Deprecated method .convertPackages()")
        res = [Package(name, urls) for name, urls in self.packages]
        res.extend(self.urls)
        return res
            
    def clean(self):
        if hasattr(self, "req"):
            self.req.close()
            del self.req