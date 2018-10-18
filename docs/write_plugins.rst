.. _write_plugins:

Plugins
=======

A Plugin is a python file located at one of the subfolders in :file:`pyload/plugins/`. Either :file:`hoster`, :file:`crypter`
or :file:`container`, depending of it's type.

There are three kinds of different plugins: **Hoster**, **Crypter**, **Container**.
All kind of plugins inherit from the base :class:`Plugin <pyload.plugins.Plugin.Plugin>`. You should know its
convenient methods, they make your work easier ;-)

Every plugin defines a ``__pattern__`` and when the user adds urls, every url is matched against the pattern defined in
the plugin. In case the ``__pattern__`` matched on the url the plugin will be assigned to handle it and instanciated when
pyLoad begins to download/decrypt the url.

Plugin header
-------------

How basic hoster plugin header could look like: ::

        from pyload.plugin.hoster import Hoster

        class MyFileHoster(Hoster):
                __name__ = "MyFileHoster"
                __version__ = "0.1"
                __pattern__ = r"http://myfilehoster.example.com/file_id/[0-9]+"
                __config__ = []

You have to define these meta-data, ``__pattern__`` has to be a regexp that sucessfully compiles with
``re.compile(__pattern__)``.

Just like :ref:`write_addons` you can add and use config values exatly the same way.
If you want a Crypter or Container plugin, just replace the word Hoster with your desired plugin type.


Hoster plugins
--------------

We head to the next important section, the ``process`` method of your plugin.
In fact the ``process`` method is the only functionality your plugin has to provide, but its always a good idea to split up tasks to not produce spaghetti code.
An example ``process`` function could look like this ::

        from pyload.plugin.hoster import Hoster

        class MyFileHoster(Hoster):
            """
                plugin code
            """

            def process(self, pyfile):
                html = self.load(pyfile.url)  #: load the content of the orginal pyfile.url to html

                # parse the name from the site and set attribute in pyfile
                pyfile.name = self.myFunctionToParseTheName(html)
                parsed_url = self.myFunctionToParseUrl(html)

                # download the file, destination is determined by pyLoad
                self.download(parsed_url)

You need to know about the :class:`PyFile <pyload.datatype.pyfile.PyFile>` class, since an instance of it is given as parameter to every pyfile.
Some tasks your plugin should handle:  proof if file is online, get filename, wait if needed, download the file, etc..

Wait times
__________

Some hoster require you to wait a specific time. Just set the time with ``self.setWait(seconds)`` or
``self.setWait(seconds, True)`` if you want pyLoad to perform a reconnect if needed.

Captcha decrypting
__________________

To handle captcha input just use ``self.decryptCaptcha(url, ...)``, it will be send to clients
or handled by :class:`Addon <pyload.plugins.internal.addon.Addon>` plugins

Crypter
-------

What about Decrypter and Container plugins?
Well, they work nearly the same, only that the function they have to provide is named ``decrypt``

Example: ::

    from pyload.plugin.crypter import Crypter

    class MyFileCrypter(Crypter):
        """
            plugin code
        """
        def decrypt(self, pyfile):

            urls = ["http://get.pyload.net/src", "http://get.pyload.net/debian", "http://get.pyload.net/win"]

            self.packages.append(("pyLoad packages", urls, "pyLoad packages")) #: urls list of urls

They can access all the methods from :class:`Plugin <pyload.plugins.Plugin.Plugin>`, but the important thing is they
have to append all packages they parsed to the `self.packages` list. Simply append tuples with `(name, urls, folder)`,
where urls is the list of urls contained in the packages. Thats all of your work, pyLoad will know what to do with them.

Examples
--------

Best examples are already existing plugins in :file:`pyload/plugins/`.