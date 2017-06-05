#Description
pyLoad is a free and open source downloader for 1-click-hosting sites
like rapidshare.com or uploaded.to.
It supports link decryption as well as all important container formats.

pyLoad is written entirely in Python and is currently under heavy development.

For news, downloads, wiki, forum and further information visit the [pyLoad website.](https://pyload.net/)

To report bugs, suggest features, ask a question, get the developer version
or help us out, go [here.](http://github.com/pyload/pyload)

Documentation about extending pyLoad can be found in the [pyLoad wiki](https://github.com/pyload/pyload/wiki) or you can join us at #pyload on irc.freenode.net

##Table of Contents
- [Dependencies](#dependencies)
 - [Required](#required)
 - [Optional](#optional)
- [First Start](#first-start)
 - [Configuration](#configuration)
 - [Adding Downloads](#adding-downloads)
- [Notes](#notes)


##Dependencies
You need at least python 2.5 to run pyLoad and all of these required libaries.
They should be automatically installed when using pip install.
The prebuilt pyload packages also install these dependencies or have them included, so manual install is only needed when installing pyLoad from source.

####Required
- pycurl a.k.a python-curl
- jinja2
- beaker
- thrift
- simplejson (for python 2.5)

Some plugins require additional packages, only install these when needed.

####Optional
- pycrypto: RSDF/CCF/DLC support
- tesseract, python-pil a.k.a python-imaging: Automatic captcha recognition for a small amount of plugins
- jsengine (spidermonkey, ossp-js, pyv8, rhino): Used for several hoster, ClickNLoad
- feedparser
- BeautifulSoup
- pyOpenSSL: For SSL connection

##First start
Note: If you installed pyload via package-manager `python pyLoadCore.py` is probably equivalent to `pyLoadCore`

Run::

    python pyLoadCore.py

and follow the instructions of the setup assistent.

For a list of options use::

    python pyLoadCore.py -h

###Configuration
After finishing the setup assistent pyLoad is ready to use and more configuration can be done via webinterface.
Additionally you could simply edit the config files located in your pyLoad home dir (defaults to: ~/.pyload)
with your favorite editor and edit the appropriate options. For a short description of
the options take a look at the [pyLoad Configuration Wiki.](https://github.com/pyload/pyload/wiki/Configuration)

To restart the configure assistant run::

    python pyLoadCore.py -s

###Adding downloads
To start the CLI and connect to a local server, run::

    python pyLoadCli.py -l

for more options refer to::

    python pyLoadCli.py -h

The web interface can be accessed when pointing your web browser to the ip and configured port, defaults to http://localhost:8000

##Notes
For more information, see the [pyLoad website.](#https://pyload.net/)
