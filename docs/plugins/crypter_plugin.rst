.. _crypter_plugin:

Crypter - Extract links from pages
==================================

What about Decrypter and Container plugins?
Well, they work nearly the same, only that the function they have to provide is named ``decrypt``

Example: ::

    from module.plugin.Crypter import Crypter

    class MyFileCrypter(Crypter):
        """
            plugin code
        """
        def decrypt(self, pyfile):

            urls = ["http://get.pyload.org/src", "http://get.pyload.org/debian", "http://get.pyload.org/win"]

            self.packages.append(("pyLoad packages", urls, "pyLoad packages")) # urls list of urls

They can access all the methods from :class:`Plugin <module.plugins.Plugin.Plugin>`, but the important thing is they
have to append all packages they parsed to the `self.packages` list. Simply append tuples with `(name, urls, folder)`,
where urls is the list of urls contained in the packages. Thats all of your work, pyLoad will know what to do with them.
