.. _write_addons:

Addon - Add new functionality
=============================

A Hook is a python file which is located at :file:`pyload/plugins/hooks`.
The :class:`HookManager <pyload.hookmanager.HookManager>` will load it automatically on startup. Only one instance exists
over the complete lifetime of pyload. Your hook can interact on various events called by the :class:`HookManager <pyload.hookmanager.HookManager>`,
do something completely autonomic and has full access to the :class:`Api <pyload.api.Api>` and every detail of pyLoad.
The UpdateManager, CaptchaTrader, UnRar and many more are implemented as hooks.

Hook header
-----------

Your hook needs to subclass :class:`Hook <pyload.plugins.hook.Hook>` and will inherit all of its methods, so make sure to check it's documentation!

All hooks should start with something like this: ::

        from pyload.plugins.hook import Hook

        class YourHook(Hook):
                __name__ = "YourHook"
                __version__ = "0.1"
                __description__ = "Does really cool stuff"
                __config__ = [ ("activated" , "bool" , "Activated"  , "True" ) ]
                __author_name__ = ("Me")
                __author_mail__ = ("me@has-no-mail.com")

All meta-data is defined in the header, you need at least one option at ``__config__`` so the user can toggle your
hook on and off. Don't overwrite the ``init`` method if not necessary, use ``setup`` instead.

Using the Config
----------------

We are taking a closer look at the ``__config__`` parameter.
You can add more config values as desired by adding tuples of the following format to the config list: ``("name", "type", "description", "default value")``.
When everything went right you can access the config values with ``self.get_config(name)`` and ``self.set_config(name, value``.


Interacting on Events
---------------------

The next step is to think about where your Hook action takes place.

The easiest way is to overwrite specific methods defined by the :class:`Hook <pyload.plugins.hook.Hook>` base class.
The name is indicating when the function gets called.
See :class:`Hook <pyload.plugins.hook.Hook>` page for a complete listing.

You should be aware of the arguments the hooks are called with, whether its a :class:`PyFile <pyload.pyfile.PyFile>`
or :class:`PyPackage <pyload.pypackage.PyPackage>` you should read the relevant documentation to know how to access it's great power and manipulate them.

What a basic excerpt would look like: ::

    from pyload.plugins.hook import Hook

    class YourHook(Hook):
        """
        Your Hook code here.
        """

        def activate(self):
            print("Yay, the core is ready let's do some work")

        def downloadFinished(self, pyfile):
            print("A Download just finished")

Another important feature to mention can be seen at the ``__threaded__`` parameter. Function names listed will be executed
in a thread, in order to not block the main thread. This should be used for all kinds of long lived processing tasks.

Another and more flexible and powerful way is to use the event listener.
All hook methods exists as event and very useful additional events are dispatched by the core. For a little overview look
at :class:`HookManager <pyload.hookmanager.HookManager>`. Keep in mind that you can define your own events and other people may listen on them.

For your convenience it's possible to register listeners automatically via the ``event_map`` attribute.
It requires a `dict` that maps event names to function names or a `list` of function names. It's important that all names are strings ::

    from pyload.plugins.hook import Hook

    class YourHook(Hook):
        """
        Your Hook code here.
        """
        event_map = {"downloadFinished" : "doSomeWork",
                     "allDownloadsFinished": "someMethod",
                     "activate": "initialize"}

        def initialize(self):
            print("Initialized")

        def doSomeWork(self, pyfile):
            print("This is equivalent to the above example")

        def someMethod(self):
            print("The underlying event (allDownloadsFinished) for this method is not available through the base class")

An advantage of the event listener is that you are able to register and remove the listeners at runtime.
Use `self.manager.listen_to("name", function)`, `self.manager.remove_event("name", function)` and see doc for
:class:`HookManager <pyload.hookmanager.HookManager>`. Contrary to ``event_map``, ``function`` has to be a reference
and **not** a `string`.

We introduced events because it scales better if there is a huge amount of events and hooks. So all future interactions will be exclusively
available as event and not accessible through overwriting hook methods. However you can safely do this, it will not be removed and is easier to implement.


Providing
 RPC services
----------------------

You may have noticed that pyLoad has an :class:`Api <pyload.api.Api>`, which can be used internal or called by clients via RPC.
So probably clients want to be able to interact with your hook to request it's state or invoke some action.

Sounds complicated but is very easy to do. Just use the ``Expose`` decorator: ::

    from pyload.plugins.hook import Hook, Expose

    class YourHook(Hook):
        """
        Your Hook code here.
        """

        @Expose
        def invoke(self, arg):
            print("Invoked with", arg)

Thats all, it's available via the :class:`Api <pyload.api.Api>` now. If you want to use it read :ref:`access_api`.
Here is a basic example: ::

    #Assuming client is a ThriftClient or Api object

    print(client.get_services())
    print(client.call(ServiceCall("YourHook", "invoke", "an argument")))

Providing status information
----------------------------
Your hook can store information in a ``dict`` that can easily be retrievied via the :class:`Api <pyload.api.Api>`.

Just store everything in ``self.info``. ::

    from pyload.plugins.hook import Hook

    class YourHook(Hook):
        """
        Your Hook code here.
        """

        def setup(self):
            self.info = {"running": False}

        def activate(self):
            self.info['running'] = True

Usable with: ::

    #Assuming client is a ThriftClient or Api object

    print(client.get_all_info())

Example
-------
    Sorry but you won't find an example here ;-)

    Look at :file:`pyload/plugins/hooks` and you will find plenty examples there.
