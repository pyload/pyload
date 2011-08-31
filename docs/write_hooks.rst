.. _write_hooks:

Hooks
=====

A Hook is a python file which is located at :file:`module/plugins/hooks`.
The :class:`HookManager <module.HookManager.HookManager>` will load it automatically on startup. Only one instance exists
over the complete lifetime of pyload. Your hook can interact on various events called by the :class:`HookManager <module.HookManager.HookManager>`,
do something complete autonomic and has full access to the :class:`Api <module.Api.Api>` and every detail of pyLoad.
The UpdateManager, CaptchaTrader, UnRar and many more are realised as hooks.

Hook header
-----------

Your hook needs to subclass :class:`Hook <module.plugins.Hook.Hook>` and will inherit all of its method, make sure to check its documentation!

All Hooks should start with something like this: ::

        from module.plugins.Hook import Hook

        class YourHook(Hook):
                __name__ = "YourHook"
                __version__ = "0.1"
                __description__ = "Does really cool stuff"
                __config__ = [ ("activated" , "bool" , "Activated"  , "True" ) ]
                __threaded__ = ["downloadFinished"]
                __author_name__ = ("Me")
                __author_mail__ = ("me@has-no-mail.com")
                
All meta-data is defined in the header, you need at least one option at ``__config__`` so the user can toggle your
hook on and off. Dont't overwrite the ``init`` method if not neccesary, use ``setup`` instead.

Using the Config
----------------

We are taking a closer look at the ``__config__`` parameter.
You can add more config values as desired by adding tuples of the following format to the config list: ``("name", "type", "description", "default value")``.
When everything went right you can access the config values with ``self.getConfig(name)`` and ``self.setConfig(name,value``.


Interacting on Events
---------------------

The next step is to think about where your Hook action takes places.

The easiest way is to overwrite specific methods defined by the :class:`Hook <module.plugins.Hook.Hook>` base class.
The name is indicating when the function gets called.
See :class:`Hook <module.plugins.Hook.Hook>` page for a complete listing.

You should be aware of the arguments the Hooks are called with, whether its a :class:`PyFile <module.PyFile.PyFile>`
or :class:`PyPackage <module.PyPackage.PyPackage>` you should read its related documentation to know how to access her great power and manipulate them.

A basic excerpt would look like: ::

    from module.plugins.Hook import Hook

    class YourHook(Hook):
        """
        Your Hook code here.
        """

        def coreReady(self):
            print "Yay, the core is ready let's do some work."

        def downloadFinished(self, pyfile):
            print "A Download just finished."

Another important feature to mention can be seen at the ``__threaded__`` parameter. Function names listed will be executed
in a thread, in order to not block the main thread. This should be used for all kind of longer processing tasks.

Another and more flexible and powerful way is to use event listener.
All hook methods exists as event and very useful additional events are dispatched by the core. For a little overview look
at :class:`HookManager <module.HookManager.HookManager>`. Keep in mind that you can define own events and other people may listen on them.

For your convenience it's possible to register listeners automatical via the ``event_map`` attribute.
It requires a `dict` that maps event names to function names or a `list` of function names. It's important that all names are strings ::

    from module.plugins.Hook import Hook

    class YourHook(Hook):
        """
        Your Hook code here.
        """
        event_map = {"downloadFinished" : "doSomeWork",
                     "allDownloadsFnished": "someMethod",
                     "coreReady": "initialize"}

        def initialize(self):
            print "Initialized."

        def doSomeWork(self, pyfile):
            print "This is equivalent to the above example."

        def someMethod(self):
            print "The underlying event (allDownloadsFinished) for this method is not available through the base class"

An advantage of the event listener is that you are able to register and remove the listeners at runtime.
Use `self.manager.addEvent("name", function)`, `self.manager.removeEvent("name", function)` and see doc for
:class:`HookManager <module.HookManager.HookManager>`. Contrary to ``event_map``, ``function`` has to be a reference
and **not** a `string`.

We introduced events because it scales better if there a a huge amount of events and hooks. So all future interaction will be exclusive
available as event and not accessible through overwriting hook methods. However you can safely do this, it will not be removed and is easier to implement.


Providing RPC services
----------------------

You may noticed that pyLoad has an :class:`Api <module.Api.Api>`, which can be used internal or called by clients via RPC.
So probably clients want to be able to interact with your hook to request it's state or invoke some action.

Sounds complicated but is very easy to do. Just use the ``Expose`` decorator: ::

    from module.plugins.Hook import Hook, Expose

    class YourHook(Hook):
        """
        Your Hook code here.
        """
        
        @Expose
        def invoke(self, arg):
            print "Invoked with", arg

Thats all, it's available via the :class:`Api <module.Api.Api>` now. If you want to use it read :ref:`access_api`.
Here is a basic example: ::

    #Assuming client is a ThriftClient or Api object

    print client.getServices()
    print client.call(ServiceCall("YourHook", "invoke", "an argument"))

Providing status information
----------------------------
Your hook can store information in a ``dict`` that can easily be retrievied via the :class:`Api <module.Api.Api>`.

Just store everything in ``self.info``. ::

    from module.plugins.Hook import Hook

    class YourHook(Hook):
        """
        Your Hook code here.
        """

        def setup(self):
            self.info = {"running": False}

        def coreReady(self):
            self.info["running"] = True

Usable with: ::

    #Assuming client is a ThriftClient or Api object

    print client.getAllInfo()

Example
-------
    Sorry but you won't find an example here ;-)
    
    Look at :file:`module/plugins/hooks` and you will find plenty examples there.
