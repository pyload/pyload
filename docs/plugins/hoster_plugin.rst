.. _hoster_plugin:

Hoster - Load files to disk
===========================

We head to the next important section, the ``process`` method of your plugin.
In fact the ``process`` method is the only functionality your plugin has to provide, but its always a good idea to split up tasks to not produce spaghetti code.
An example ``process`` function could look like this ::

        from module.plugin.Hoster import Hoster

        class MyFileHoster(Hoster):
            """
                plugin code
            """
            
            def process(self, pyfile):
                html = self.load(pyfile.url)  # load the content of the orginal pyfile.url to html

                # parse the name from the site and set attribute in pyfile
                pyfile.name = self.myFunctionToParseTheName(html)
                parsed_url = self.myFunctionToParseUrl(html)

                # download the file, destination is determined by pyLoad
                self.download(parsed_url)

You need to know about the :class:`PyFile <module.PyFile.PyFile>` class, since an instance of it is given as a parameter to every pyfile.
Some tasks your plugin should handle:  check if the file is online, get filename, wait if needed, download the file, etc..

Wait times
----------

Some hosters require you to wait a specific time. Just set the time with ``self.setWait(seconds)`` or
``self.setWait(seconds, True)`` if you want pyLoad to perform a reconnect if needed.

Captcha decrypting
------------------

To handle captcha input just use ``self.decryptCaptcha(url, ...)``, it will be send to clients
or handled by :class:`Hook <module.plugins.Hook.Hook>` plugins

User interaction
----------------


SimpleHoster
------------


Testing
-------


Examples
--------

The best examples are the already existing plugins in :file:`module/plugins/`.