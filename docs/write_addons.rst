.. _write_addons:

Addons
======

A Addon is a python file which is located at :file:`pyload/plugins/addon`.
The :class:`AddonManager <pyload.manager.AddonManager.AddonManager>` will load it automatically on startup. Only one instance exists
over the complete lifetime of pyload. Your addon can interact on various events called by the :class:`AddonManager <pyload.manager.AddonManager.AddonManager>`,
do something complete autonomic and has full access to the :class:`Api <pyload.api.Api>` and every detail of pyLoad.
The UpdateManager, CaptchaTrader, UnRar and many more are realised as addons.

addon header
-----------

Your addon needs to subclass :class:`addon <pyload.plugins.addon.addon>` and will inherit all of its method, make sure to check its documentation!

All Addons should start with something like this: ::

        from pyload.plugins.addon import addon

        class YourAddon(addon):
                __name__ = "YourAddon"
                __version__ = "0.1"
                __description__ = "Does really cool stuff"
                __config__ = [ ("enabled" , "bool" , "Activated"  , "True" ) ]
                __threaded__ = ["downloadFinished"]
                __author_name__ = ("Me")
                __author_mail__ = ("me@has-no-mail.com")

All meta-data is defined in the header, you need at least one option at ``__config__`` so the user can toggle your
addon on and off. Dont't overwrite the ``init`` method if not neccesary, use ``setup`` instead.

Using the Config
----------------

We are taking a closer look at the ``__config__`` parameter.
You can add more config values as desired by adding tuples of the following format to the config list: ``("name", "type", "description", "default value")``.
When everything went right you can access the config values with ``self.getConfig(name)`` and ``self.setConfig(name,value``.


Interacting on Events
---------------------

The next step is to think about where your addon action takes places.

The easiest way is to overwrite specific methods defined by the :class:`addon <pyload.plugins.addon.addon>` base class.
The name is indicating when the function gets called.
See :class:`addon <pyload.plugins.addon.addon>` page for a complete listing.

You should be aware of the arguments the Addon are called with, whether its a :class:`PyFile <pyload.datatype.pyfile.PyFile>`
or :class:`PyPackage <pyload.datatype.pypackage.PyPackage>` you should read its related documentation to know how to access her great power and manipulate them.

A basic excerpt would look like: ::

    from pyload.plugins.addon import addon

    class YourAddon(addon):
        """
        Your addon code here.
        """

        def coreReady(self):
            print("Yay, the core is ready let's do some work.")

        def downloadFinished(self, pyfile):
            print("A Download just finished.")

Another important feature to mention can be seen at the ``__threaded__`` parameter. Function names listed will be executed
in a thread, in order to not block the main thread. This should be used for all kind of longer processing tasks.

Another and more flexible and powerful way is to use event listener.
All addon methods exists as event and very useful additional events are dispatched by the core. For a little overview look
at :class:`AddonManager <pyload.manager.AddonManager.AddonManager>`. Keep in mind that you can define own events and other people may listen on them.

For your convenience it's possible to register listeners automatical via the ``event_map`` attribute.
It requires a `dict` that maps event names to function names or a `list` of function names. It's important that all names are strings ::

    from pyload.plugins.addon import addon

    class YourAddon(addon):
        """
        Your addon code here.
        """
        event_map = {"downloadFinished" : "doSomeWork",
                     "allDownloadsFnished": "someMethod",
                     "coreReady": "initialize"}

        def initialize(self):
            print("Initialized.")

        def doSomeWork(self, pyfile):
            print("This is equivalent to the above example.")

        def someMethod(self):
            print("The underlying event (allDownloadsFinished) for this method is not available through the base class")

An advantage of the event listener is that you are able to register and remove the listeners at runtime.
Use `self.m.addEvent("name", function)`, `self.m.removeEvent("name", function)` and see doc for
:class:`AddonManager <pyload.manager.AddonManager.AddonManager>`. Contrary to ``event_map``, ``function`` has to be a reference
and **not** a `string`.

We introduced events because it scales better if there a a huge amount of events and addons. So all future interaction will be exclusive
available as event and not accessible through overwriting addon methods. However you can safely do this, it will not be removed and is easier to implement.


Providing RPC services
----------------------

You may noticed that pyLoad has an :class:`Api <pyload.api.Api>`, which can be used internal or called by clients via RPC.
So probably clients want to be able to interact with your addon to request it's state or invoke some action.

Sounds complicated but is very easy to do. Just use the ``Expose`` decorator: ::

    from pyload.plugins.addon import addon, Expose

    class YourAddon(addon):
        """
        Your addon code here.
        """

        @Expose
        def invoke(self, arg):
            print("Invoked with", arg)

Thats all, it's available via the :class:`Api <pyload.api.Api>` now. If you want to use it read :ref:`access_api`.
Here is a basic example: ::

    #Assuming client is a ThriftClient or Api object

    print(client.getServices())
    print(client.call(ServiceCall("YourAddon", "invoke", "an argument")))

Providing status information
----------------------------
Your addon can store information in a ``dict`` that can easily be retrievied via the :class:`Api <pyload.api.Api>`.

Just store everything in ``self.info``. ::

    from pyload.plugins.addon import addon

    class YourAddon(addon):
        """
        Your addon code here.
        """

        def setup(self):
            self.info = {"running": False}

        def coreReady(self):
            self.info["running"] = True

Usable with: ::

    #Assuming client is a ThriftClient or Api object

    print(client.getAllInfo())

Example
-------
    Sorry but you won't find an example here ;-)

    Look at :file:`pyload/plugins/addon` and you will find plenty examples there.
