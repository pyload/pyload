![pyLoad](/logo.png "pyLoad")
=============================

**pyLoad** is a free and open source download manager for all kind of operating systems and devices,
designed to be extremely lightweight and runnable on common computers or headless servers.

Its modern web interface allows to manage downloads across networks and easily access them from anywhere.
All common video-sites, one-click-hosters, container formats and well known web standards are supported to download files for you.
Additionaly it has a great variety of plugins to automate common tasks and make unattended running possible.

pyLoad has a full featured and well documented API, is easily extendable and accessible by external tools.
It is written entirely in Python and under heavy development.


Dependencies
------------

**You need at least python 2.5 to run pyLoad and all of these required libaries.**
They should be automatically installed when using pip install.
The pre-built pyload packages also install these dependencies or have them included, so manual install
is only needed when installing pyLoad from source.

### Required ###

 - **beaker**
 - **jinja2**
 - **pycurl** (a.k.a python-curl)
 - **simplejson**: For python 2.5
 - **thrift**

Some plugins require additional packages, install these only when needed.

### Optional ###

 - **BeautifulSoup**
 - **feedparser**
 - **jsengine** (spidermonkey, ossp-js, pyv8, rhino): Needed by several hosters (ex.: ClickNLoad)
 - **pycrypto**: For RSDF/CCF/DLC support
 - **pyOpenSSL**: For SSL connection
 - **tesseract**, **python-pil** (a.k.a python-imaging): For automatic captcha recognition support


First start
-----------

***Note:***
If you installed pyload via package-manager `python pyLoadCore.py` is probably equivalent to `pyLoadCore`.

Run:

    python pyLoadCore.py

and follow the instructions of the setup assistant.

For a list of options use:

    python pyLoadCore.py -h


Configuration
-------------

After finishing the setup assistant pyLoad is ready to use and more configuration can be done via webinterface.
Additionally you could simply edit the configuration files located in your pyLoad home directory (default to `~/.pyload`)
with your favorite editor and edit the appropriate options. For a short description of
the options take a look at <http://pyload.org/configuration>.

To restart the configure assistant run:

    python pyLoadCore.py -s

### Adding downloads ###

To start the Command Line Interface and connect to a local server, run:

    python pyLoadCli.py -l

for more options refer to:

    python pyLoadCli.py -h

The webinterface can be accessed when pointing your webbrowser to the IP and configured port, defaults to `http://localhost:8000`.


Notes
-----

For news, downloads, wiki, forum and further information visit <http://pyload.org/>.

To report bugs, suggest features, ask a question, get the developer version
or help us out, visit <https://github.com/pyload/pyload>.

Documentation about extending pyLoad can be found at <http://docs.pyload.org> or joining us at `#pyload` on `irc.freenode.net`.


------------------------------
###### pyLoad Team 2008-2014 ######
