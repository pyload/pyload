.. _crypter_plugin:

Crypter - Extract links from pages
==================================

We are starting with the simplest plugin, the :class:`Crypter <module.plugins.Crypter.Crypter>`.
It's job is it to take a url as input and generate new package or links, for example by filtering the urls or
loading a page and extracting links from the html code. You need to define the ``__pattern__`` to match
target urls and subclass from :class:`Crypter <module.plugins.Crypter.Crypter>`. ::

    from module.plugin.Crypter import Crypter

    class MyFileCrypter(Crypter):
        __pattern__ = r"mycrypter.com/id/([0-9]+)"

        def decryptURL(self, url):

            urls = ["http://get.pyload.org/src", "http://get.pyload.org/debian", "http://get.pyload.org/win"]
            return urls

You have to overwrite at least one of ``.decryptFile``, ``.decryptURL``, ``.decryptURLs``. The first one
is only useful for container files, whereas the last is useful when it's possible to handle a bunch of urls
at once. If in doubt, just overwrite `decryptURL`.

Generating Packages
-------------------

When finished with decrypting just return the urls as list and they will be added to the package. You can also
create new Packages if needed by instantiating a :class:`Package` instance, which will look like the following::

    from module.plugin.Crypter import Crypter, Package

    class MyFileCrypter(Crypter):

        def decryptURL(self, url):

            html = self.load(url)

            # .decrypt_from_content is only a example method here and will return a list of urls
            urls = self.decrypt_from_content(html)
            return Package("my new package", urls)

And that's basically all you need to know. Just as little side-note if you want to use decrypter in
your code you can use::

        plugin = self.core.pluginManager.loadClass("crypter", "NameOfThePlugin")
        # Core instance is needed for decrypting
        # decrypted will be a list of urls
        decrypted = plugin.decrypt(core, urls)


SimpleCrypter
-------------

For simple crypter services there is the :class:`SimpleCrypter <module.plugins.internal.SimpleCrypter.SimpleCrypter>` class which handles most of the workflow. Only the regexp
pattern have to be defined.

Exmaple::

    from module.plugins.internal.SimpleCrypter import SimpleCrypter

        class MyFileCrypter(SimpleCrypter):

Testing
-------

Please append a test link at :file:`tests/crypterlinks.txt` followed by `||xy`, where xy is the number of
expected links/packages to extract.
Our testrunner will be able to check your plugin periodical for functionality.