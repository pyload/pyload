.. _base_plugin:

Base Plugin - And here it begins...
===================================

A Plugin in pyLoad is a python file located at one of the subfolders in :file:`pyload/plugins/`.
All different plugin types inherit from :class:`Base <pyload.plugins.base.Base>`, which defines basic methods
and meta data. You should read this section carefully, because it's the base for all plugin development. It
is also a good idea to look at the class diagram [1]_ for all plugin types to get an overview.
At last you should look at several already existing plugin to get a more detailed idea of how
they have to look like and what is possible with them.

Meta Data
---------

All important data which must be known by pyLoad is set using class attributes pre- and suffixed with ``__``.
An overview of acceptable values can be found in :class:`Base <pyload.plugins.base.Base>` source code.
Unneeded attributes can be left out, except ``__version__``. Nevertheless please fill out most information
as you can, when you want to submit your plugin to the public repository.

Additionally :class:`Crypter <pyload.plugins.crypter.Crypter>` and :class:`Hoster <pyload.plugins.hoster.Hoster>`
needs to have a specific regexp [2]_ ``__pattern__``. This will be matched against input url's and if a suited
plugin is found it is selected to handle the url.

For localization pyLoad supports gettext [3]_, to mark strings for translation surround them with ``_("...")``.

You do not need to subclass :class:`Base <pyload.plugins.base.Base>` directly, but the
intermediate type according to your plugin. As an example we choose a hoster plugin, but the same is true for all
plugin types.

How a basic hoster plugin header could look like::

        from pyload.plugin.hoster import Hoster

        class MyFileHoster(Hoster):
                __version__ = "0.1"
                __description__ = _("Short description of the plugin")
                __long_description = _("""An even longer description
                is not needed for hoster plugins,
                but an addon plugin should have it, so the users know what it is doing.""")

In future examples the meta data will be left out, but remember it's required in every plugin!

Config Entries
--------------

Every plugin is allowed to add entries to the configuration. These are defined via ``__config__`` and consist
of a list with tuples in the format of ``(name, type, verbose_name, default_value)`` or
``(name, type, verbose_name, short_description, default_value)``.

Example from Youtube plugin::

        class YoutubeCom:
            __config__ = [("quality", "sd;hd;fullhd", _("Quality Setting"), "hd"),
                          ("fmt", "int", _("FMT Number 0-45"), _("Desired FMT number, look them up at wikipedia"), 0),
                          (".mp4", "bool", _("Allow .mp4"), True)]


At runtime the desired config values can be retrieved with ``self.get_config(name)`` and set with
``self.set_config(name, value)``.

Tagging Guidelines
------------------

To categorize a plugin, a list of keywords can be assigned via ``__tags__`` attribute. You may add arbitrary
tags as you like, but please look at this table first to choose your tags. With standardised keywords we can generate
a better overview of the plugins and provide some search criteria.

=============== =================================================================
Keyword         Meaning
=============== =================================================================
image           Anything related to image(hoster)
video           Anything related to video(hoster)
captcha         A plugin that needs captcha decrypting
interaction     A plugin that makes use of interaction with the user
free            A hoster without any premium service
premium_only    A hoster only usable with account
ip_check        A hoster that checks ip, that can be avoided with reconnect
=============== =================================================================

Basic Methods
-------------

All methods can be looked up at :class:`Base <pyload.plugins.base.Base>`. To note some important ones:

The pyload core instance is accessible at ``self.pyload`` attribute
and the :class:`Api <pyload.api.Api>` at ``self.pyload.api``

With ``self.load(...)`` you can load any url and get the result. This method is only available to Hoster and Crypter.
For other plugins use ``getURL(...)`` or ``get_request()``.

Use ``self.store(...)`` and ``self.retrieve(...)`` to store data persistently into the database.

Make use of ``log_info, log_error, log_warning, log_debug`` for logging purposes.

Debugging
---------

One of the most important aspects in software programming is debugging. It is especially important
for plugins which heavily rely on external input, which is true for all hoster and crypter plugins.
To enable debugging functionality start pyLoad with the ``-d`` option or enable it in the config.

You should use ``self.log_debug(msg)`` when ever it is reasonable. It is a good pratice to log server output
or the calculation of results and then check in the log if it really is what you are expecting.

For further debugging you can install ipython [4]_, and set breakpoints with ``self.pyload.breakpoint()``.
It will open the python debugger [5]_ and pause the plugin thread.
To open a ipython shell in the running programm use ``self.shell()``.
These methods are useful to gain access to the code flow at runtime and check or modify variables.


.. rubric:: Footnotes
.. [1] :ref:`plugin_hierarchy`
.. [2] http://docs.python.org/library/re.html
.. [3] http://docs.python.org/library/gettext.html
.. [4] http://ipython.org/
.. [5] http://docs.python.org/library/pdb.html
