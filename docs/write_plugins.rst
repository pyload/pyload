.. _write_plugins:                                                                                                                  

********************
How to extend pyLoad                                                                                                                
********************

This page should give you an basic idea, how to extend pyLoad with new features!

Hooks
-----

A Hook is a module which is located at :file:`module/plugin/hooks` and loaded with the startup. It inherits all methods from the base :class:`Hook <module.plugins.Hook.Hook>` module, make sure to check its documentation!

All Hooks should start with something like this: ::

        from module.plugins.Hook import Hook

        class YourHook(Hook):
                __name__ = "My own Hook"
                __version__ = "0.1" 
                __description__ = "Does really cool stuff"
                __config__ = [ ("activated" , "bool" , "Activated"  , "True" ) ]
                __threaded__ = ["downloadFinished"]
                __author_name__ = ("Me")
                __author_mail__ = ("me@has-no-mail.com")
        
                def setup(self):
                        #init hook and other stuff here
                        pass

Take a closer look at the ``__config__`` parameter. You need at least this option indicating whether your Hook is activated or not.
You can add more config values as desired by adding tuples of the following format to the config list: ``("name", "type", "description", "default value")``.
When everything went right you can access your config values with ``self.getConfig(name)``.

The next step is to think about where your Hook action takes places.
You can overwrite several methods of the base plugin, her name indicates when they gets called.
See :class:`Hook <module.plugins.Hook.Hook>` page for a complete listing.

You should be aware of the arguments the Hooks are called with, whether its a :class:`PyFile <module.FileDatabase.PyFile>` or :class:`PyPackage <module.FileDatabase.PyPackage>` you should read its related documentation to know how to access her great power and manipulate them.

Another important feature to mention can be seen at the ``__threaded__`` parameter. Function names listed will be executed in a thread, in order to not block the main thread. This should be used for all kind of longer processing tasks.

        
Plugins
-------

A Plugin in pyLoad sense is a module, that will be loaded and executed when its pattern match to a url that was been added to pyLoad.

There are three kinds of different plugins: **Hoster**, **Crypter**, **Container**.
All kind of plugins inherit from the base :class:`Plugin <module.plugins.Plugin.Plugin>`. You should know its convenient methods, they make your work easier ;-)

We take a look how basis hoster plugin header could look like: ::

        from module.plugin.Hoster import Hoster
        
        class MyFileHoster(Hoster):
                __name__ = "MyFileHoster"
                __version__ = "0.1"
                __pattern__ = r"http://myfilehoster.example.com/file_id/[0-9]+"
                __config__ = []

Thats it, like above with :ref:`Hooks` you can add config values exatly the same way.

The ``__pattern__`` property is very important, it will be checked against every added url and if it matches your plugin will be choosed to do the grateful task of processing this download! In case you dont already spotted it, ``__pattern__`` has to be a regexp of course.

We head to the next important section, the ``process`` method of your plugin.
In fact the ``process`` method is the only functionality your plugin has to provide, but its always a good idea to split up tasks to not produce spaghetti code.
An example ``process`` function could look like this :: 

        def process(self, pyfile):
                html = self.load(pyfile.url)  #load the content of the orginal pyfile.url to html

                pyfile.name = self.myFunctionToParseTheName(html)  #parse the name from the site and write it to pyfile
                parsed_url = self.myFunctionToParseUrl(html)

                self.download(parsed_url)  # download the file

You need to know about the :class:`PyFile <module.FileDatabase.PyFile>` class, since a instance of it is given as parameter to every pyfile.
Some tasks your plugin should handle:  proof if file is online, get filename, wait if needed, download the file, etc..

There are also some functions to mention which are provided by the base Plugin: ``self.wait()``, ``self.decryptCaptcha()``
Read about there functionality in the :class:`Plugin <module.plugins.Plugin.Plugin>` doc.

What about Decrypter and Container plugins?
Well, they work nearly the same, only that the function they have to provide is named ``decrypt``

Example: :: 

	def decrypt(self, pyfile):
		self.packages.append((name, urls, folder)) # urls list of urls

They can access all the methods from :class:`Plugin <module.plugins.Plugin.Plugin>`, but the important thing is they have to append all packages they parsed to the `self.packages` list. Simply append tuples with `(name, urls, folder)`, where urls is the list of urls contained in the packages. Thats all of your work, pyLoad will know what to do with them.
