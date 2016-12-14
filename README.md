# pyLoad [![Build Status](http://nightly.pyload.net/buildStatus/icon?job=Nightly)](http://nightly.pyload.net/job/Nightly/)

pyLoad is a free and open source personal cloud storage as well as download manager
for all kind of operating systems and devices, designed to be extremely lightweight and
runnable on personal pc or headless server.

You can easily manage your files, downloads, media content and access it from anywhere.
All common video-sites, one-click-hoster, container formats and well known web standards are supported to download files for you.
Additionaly it has a great variety of plugins to automate common tasks and make unattended running possible.

pyLoad has a full featured and well documented API, is easily extendable and accessible
by external tools. It is written entirely in Python and currently under heavy development.

For news, downloads, wiki, forum and further information visit https://pyload.net/

To report bugs, suggest features, ask a question, get the developer version
or help us out, visit https://github.com/pyload/pyload

Documentation about extending pyLoad can be found at http://docs.pyload.net or join us at #pyload on irc.freenode.net

Dependencies
------------

You need at least python 2.6 to run pyLoad and all of these required libaries.
They should be automatically installed when using pip install.
The prebuilt pyload packages also install these dependencies or have them included, so manual install
is only needed when installing pyLoad from source.

### Required

- pycurl a.k.a python-curl
- beaker

Some plugins require additional packages, only install these when needed.

### Optional

- pycrypto: RSDF/CCF/DLC support
- tesseract, python-pil a.k.a python-imaging: Automatic captcha recognition for a small amount of plugins
- jsengine (spidermonkey, ossp-js, pyv8, rhino): Used for several hoster, ClickNLoad
- feedparser
- BeautifulSoup
- pyOpenSSL: For SSL connection

First start
-----------

Note: If you installed pyload via package-manager `python pyLoadCore.py` is probably equivalent to `pyLoadCore`

Run::

    python pyload.py

and follow the instructions of the setup assistent.

For a list of options use::

    python pyload.py -h

Configuration
-------------

After finishing the setup assistent pyLoad is ready to use and more configuration can be done via webinterface.
Additionally you could simply edit the config files located in your pyLoad home dir (defaults to: ~/.pyload)
with your favorite editor and edit the appropriate options. For a short description of
the options take a look at https://pyload.net/configuration.

To restart the configure assistent run::

    python pyload.py -s

### Adding downloads

To start the CLI and connect to a local server, run::

    python pyload-cli.py -l

for more options refer to::

    python pyload-cli.py -h

The webinterface can be accessed when pointing your webbrowser to the ip and configured port, defaults to http://localhost:8000

Notes
-----
For more information, see https://pyload.net/
