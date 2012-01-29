.. _base_plugin:

Base Plugin - And here it begins...
===================================

A Plugin in pyLoad is a python file located at one of the subfolders in :file:`module/plugins/`.
All different plugin types inherit from :class:`Base <module.plugins.Base.Base>`, which defines basic methods
and meta data. You should read this section carefully, because it's the base for all plugin development.
After that it is a good idea to look at several already existing plugin to get a more detailed idea of how
they have to look like and whats possible with them.

Meta Data
---------

All important data which must be known by pyLoad is set using class attributes pre- and suffixed with ``__``.
An overview of acceptible values can be found in :class:`Base <module.plugins.Base.Base>` source code.
Non needed attributes can be left out, except ``__version__``. Nevertheless please fill out most information
as you can, when you want to submit your plugin to the public repo.

Additionally :class:`Crypter <module.plugins.Crypter.Crypter>` and :class:`Crypter <module.plugins.Hoster.Hoster>`
needs to have a specific regexp [1]_ ``__pattern__``. This will be matched against input urls and if a suited
plugin is found it is selected to handle the url.

You don't need to subclass :class:`Base <module.plugins.Base.Base>` directly, but the
intermediate type according to your plugin. As example we choose an Hoster plugin, but the same is true for all
plugin types.

For localization pyLoad supports gettext [2]_, to mark strings for translation surround them with ``_("...")``.

How basic hoster plugin header could look like::

        from module.plugin.Hoster import Hoster

        class MyFileHoster(Hoster):
                __version__ = "0.1"
                __description__ = _("Short description of the plugin")
                __long_description = _("""A even longer description
                is not needed for hoster plugin,
                but hook plugin should have it so the user knows what they doing.""")

In future examples the meta data will be left out, but remember it's required in every plugin!

Config Entries
--------------

Every plugin is allowed to add entries to the config. These are defined via ``__config__`` and consists
of a list with tuples in the format of ``(name, type, verbose_name, default_value)`` or
``(name, type, verbose_name, short_description, default_value)``.

Example from Youtube plugin::

        class YoutubeCom:
            __config__ = [("quality", "sd;hd;fullhd", _("Quality Setting"), "hd"),
                          ("fmt", "int", _("FMT Number 0-45"), _("Desired FMT number, look them up at wikipedia"), 0),
                          (".mp4", "bool", _("Allow .mp4"), True)]


At runtime the desired config values can be retrieved with ``self.getConfig(name)`` and setted with
``self.setConfig(name, value)``.

Tagging Guidelines
------------------

To categorize a plugin, a list of keywords can be assigned via ``__tags__`` attribute. You may add arbitrary
tags as you like, but please look at this table first to choose your tags. With standardised keywords we can generate
a better overview of the plugins and provide some search criteria.

=============== ===========================================================
Keyword         Meaning
=============== ===========================================================
image           Anything related to image(hoster)
video           Anything related to video(hoster)
captcha         A plugin that needs captcha decrypting
interaction     A plugin that makes uses of interaction with user
free            A hoster without any premium service
premium_only    A hoster only useable with account
ip_check        A hoster that checks ip, that can be avoided with reconnect
=============== ===========================================================

Basic Methods
-------------

All methods can be looked up at :class:`Base <module.plugins.Base.Base>`. To note some important ones:

The pyload core instance is accessible at ``self.core`` attribute
and the :class:`Api <module.Api.Api>` at ``self.core.api``

With ``self.load(...)`` you can load any url and get the result. This method is only available to Hoster and Crypter.
For other plugins use ``getURL(...)`` or ``getRequest()``.

Use ``self.store(...)`` and ``self.retrieve(...)`` to store data persistantly into the database.

Make use of ``logInfo, logError, logWarning, logDebug`` for logging purposes.

Debugging
---------

One of the most important aspects in software programming is debugging. It is especially important
for plugins which heavily rely on external input, which is true for all hoster and crypter plugins.
To enable debugging functionality start pyLoad with ``-d`` option or enable it in the config.

You should use ``self.logDebug(msg)`` when ever it is reasonable. It is a good pratice to log server output
or the calculation of results and then check in the log if it really it what you are expecting.

For further debugging you can install ipython [3]_, and set breakpoints with ``self.core.breakpoint()``.
It will open the python debugger [4]_ and pause the plugin thread.
To open a ipython shell in the running programm use ``self.shell()``.
These methods are usefull to gain access to the code flow at runtime and check or modify variables.


.. rubric:: Footnotes
.. [1] http://docs.python.org/library/re.html
.. [2] http://docs.python.org/library/gettext.html
.. [3] http://ipython.org/
.. [4] http://docs.python.org/library/pdb.html