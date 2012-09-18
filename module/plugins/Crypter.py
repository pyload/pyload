# -*- coding: utf-8 -*-

from traceback import print_exc

from module.common.packagetools import parseNames
from module.utils import to_list, has_method, uniqify
from module.utils.fs import exists, remove, fs_encode

from Base import Base, Retry

class Package:
    """ Container that indicates that a new package should be created """
    def __init__(self, name, urls=None):
        self.name = name
        self.urls = urls if urls else []
        # nested packages
        self.packs = []

    def addURL(self, url):
        self.urls.append(url)

    def addPackage(self, pack):
        self.packs.append(pack)

    def getAllURLs(self):
        urls = self.urls
        for p in self.packs:
            urls.extend(p.getAllURLs())
        return urls

    # same name and urls is enough to be equal for packages
    def __eq__(self, other):
        return self.name == other.name and self.urls == other.urls

    def __repr__(self):
        return u"<CrypterPackage name=%s, links=%s, packs=%s" % (self.name, self.urls, self.packs)

    def __hash__(self):
        return hash(self.name) ^ hash(frozenset(self.urls))

class PyFileMockup:
    """ Legacy class needed by old crypter plugins """
    def __init__(self, url, pack):
        self.url = url
        self.name = url
        self._package = pack
        self.packageid = pack.id if pack else -1

    def package(self):
        return self._package

class Crypter(Base):
    """
    Base class for (de)crypter plugins. Overwrite decrypt* methods.

    How to use decrypt* methods:

    You have to overwrite at least one method of decryptURL, decryptURLs, decryptFile.

    After decrypting and generating urls/packages you have to return the result.
    Valid return Data is:

    :class:`Package` instance Crypter.Package
        A **new** package will be created with the name and the urls of the object.

    List of urls and `Package` instances
        All urls in the list will be added to the **current** package. For each `Package`\
        instance a new package will be created.

    """

    #: Prefix to annotate that the submited string for decrypting is indeed file content
    CONTENT_PREFIX = "filecontent:"

    @classmethod
    def decrypt(cls, core, url_or_urls):
        """Static method to decrypt urls or content. Can be used by other plugins.
        To decrypt file content prefix the string with ``CONTENT_PREFIX `` as seen above.

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
                ret.extend(url_or_pack.getAllURLs())
            else: # single url
                ret.append(url_or_pack)
        # eliminate duplicates
        return uniqify(ret)

    def __init__(self, core, package=None, password=None):
        Base.__init__(self, core)
        self.req = core.requestFactory.getRequest(self.__name__)

        # Package the plugin was initialized for, don't use this, its not guaranteed to be set
        self.package = package
        #: Password supplied by user
        self.password = password
        #: Propose a renaming of the owner package
        self.rename = None

        # For old style decrypter, do not use these!
        self.packages = []
        self.urls = []
        self.pyfile = None

        self.init()

    def init(self):
        """More init stuff if needed"""

    def setup(self):
        """Called everytime before decrypting. A Crypter plugin will be most likely used for several jobs."""

    def decryptURL(self, url):
        """Decrypt a single url

        :param url: url to decrypt
        :return: See :class:`Crypter` Documentation
        """
        if url.startswith("http"): # basic method to redirect
            return self.decryptFile(self.load(url))
        else:
            self.fail(_("Not existing file or unsupported protocol"))

    def decryptURLs(self, urls):
        """Decrypt a bunch of urls

        :param urls: list of urls
        :return: See :class:`Crypter` Documentation
        """
        raise NotImplementedError

    def decryptFile(self, content):
        """Decrypt file content

        :param content: content to decrypt as string
        :return: See :class:`Crypter` Documentation
        """
        raise NotImplementedError

    def generatePackages(self, urls):
        """Generates :class:`Package` instances and names from urls. Useful for many different links and no\
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

        # separate local and remote files
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
            result = []
            for url in urls:
                self.pyfile = PyFileMockup(url, self.package)
                self.setup()
                self.decrypt(self.pyfile)
                result.extend(self.convertPackages())
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
        """Catches all exceptions in decrypt methods and return results

        :return: Decrypting results
        """
        try:
            return self._decrypt(urls)
        except Exception:
            if self.core.debug:
                print_exc()
            return []

    def getLocalContent(self, urls):
        """Load files from disk and separate to file content and url list

        :param urls:
        :return: list of (filename, content), remote urls
        """
        content = []
        # do nothing if no decryptFile method
        if hasattr(self.__class__, "decryptFile"):
            remote = []
            for url in urls:
                path = None
                if url.startswith("http"): # skip urls directly
                    pass
                elif url.startswith(self.CONTENT_PREFIX):
                    path = url
                elif exists(url):
                    path = url
                elif exists(self.core.path(url)):
                    path = self.core.path(url)

                if path:
                    try:
                        if path.startswith(self.CONTENT_PREFIX):
                            content.append(("", path[len(self.CONTENT_PREFIX)]))
                        else:
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