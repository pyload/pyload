[![pyLoad](/docs/resources/banner.png "pyLoad")](http://pyload.org/)
====================================================================

[![Translation Status](http://translate.pyload.org/badges/pyload/localized.png "Translation Status")](http://translate.pyload.org/project/pyload/)

**pyLoad** is a Free and Open Source download manager written in Python and designed to be extremely lightweight.

pyLoad is available for all kind of operating systems and devices:
You could install it on a computer, but also on a headless servers, a router, a smart usb-stick running linux... almost whatever you want!

You can control it entirely by web.
Its web user interface allows full managing and easily remote access to your download from anywhere, online, or in your personal network..

All common video-sites, one-click-hosters, container formats and well known web standards are supported to allow you to download files.
Additionaly, pyLoad has a great variety of plugins to automate common tasks and make unattended running possible.

pyLoad has a fully featured and well documented API, it's easily extendable and accessible by external tools, cross-platform apps or other softwares.


Download & Installation
-----------------------

You can see all the pre-build packages of pyLoad here: <https://github.com/pyload/pyload/releases>.

> **Note:**
If you're on Windows, it's highly recommended to install the pre-build package instead getting the source code.

Pre-build packages yet included all the software dependencies required to run pyLoad.

By the way, you can install any missing software packages by the Python Package Index, typing:

    pip install <package-name>

You can download the latest stable source code here: <>.
You can download the latest development source code here: <>.


Dependencies
------------

 - **You need at least Python 2.5 or at most Python 2.7 to run pyLoad and its required software packages**
 - **Python 3 and PyPy are not yet supported**

### Required ###

 - **Beaker**
 - **Getch**
 - **MultipartPostHandler**
 - **SafeEval**
 - **bottle**
 - **colorama**
 - **jinja2**
 - **markupsafe**
 - **pycurl** (python-curl)
 - **rename_process**
 - **setuptools**
 - **thrift**
 - **wsgiserver**


Some extra features require additional software packages. See below:

### Optional ###

 - **BeautifulSoup**                                  *Few plugins support*
 - **PIL** (python-imaging)                           *Captcha recognition*
 - **colorlog**                                       *Colored log*
 - **bjoern** (<https://github.com/jonashaag/bjoern>) *More responsive web interface*
 - **feedparser**                                     *RSS parsing*
 - **node.js**                                        *ClickNLoad and other plugins*
   - or **ossp-js**
   - or **pyv8**
   - or **rhino**
   - or **spidermonkey**
 - **pyOpenSSL**                                      *SSL support*
 - **pycrypto**                                       *RSDF/CCF/DLC decrypting*
 - **simplejson**                                     *JSON speedup*
 - **tesseract**                                      *Captcha OCR support*


Translations
------------

The localization process take place on Crowdin: <http://crowdin.net/project/pyload>.


### Send a tip for translators ###

If you want to explain a translatable string to make the translation process easier you can do that using comment block starting with `L10N:`. For example:

    python
    # L10N: Here the tip for translators
    # Thanks
    print _("A translatable string")

Translators will see:

    L10N: Here the tip for translators
    Thanks


### Updating templates ###

To update POT files type:

    paver generate_locale

To automatically upload the updated POTs on Crowdin for the localization process just type:

    paver upload_translations -k [api_key]

the API Key can be retrieved in the Settings panel of the project on Crowdin. This is allowed only to the administrators.


### Retrieve PO files ###

Updated PO files can be automatically download from Crowdin typing:

    paver download_translations -k [api_key]

This is allowed only to administrators, **users can download the last version of the translations using the Crowdin web interface**.


### Compile PO files ###

MO files can be generated typing:

    paver compile_translations

To compile a single file just use command `msgfmt`.
For example to compile a core.po file type:

    msgfmt -o core.mo core.po


Usage
-----

### First Start ###

Run:

    python pyload.py

and follow the setup assistant instructions.

> **Note:**
If you installed pyLoad by a package-manager, command `python pyload.py` might be equivalent to `pyload`.

If something go wrong, you can restart the setup assistant whenever you want, just typing:

    python pyload.py -s

Or you can even edit configuration files located in your pyLoad home directory (default to `~/.pyload`)
with your favorite editor.
For a short description of all the configuration options available visit <http://pyload.org/configuration>.


### Web User Interface ###

Run:

    python pyload.py

So, to retrieve it point your browser to the socket address configured by setup (default to `http://localhost:8000`).

You can get the list of accepted arguments typing:

    python pyload.py -h


### Command Line Interface ###

Run:

    python pyload-cli.py -l

You can get the list of accepted arguments typing:

    python pyload-cli.py -h


Licensing
---------

### pyLoad  ###

Refer to the attached file **LICENSE.md** for the extended license.


### Plugin  ###

According to the terms of the pyLoad license, pyload's plugins must be treated as an extension of the main program.
This means that all the plugins must be released under the same license of pyLoad (or a compatible
one) to be included in the official repository and released with pyLoad:

 * Any plugin published **without a license notice** is intend published under the pyLoad license.
 * A different license can be used but it **must be compatible** to the pyLoad license.
 * Any plugin published **with a incompatible license** will be rejected.

 * Is recommended to put a **shorten** license notice over the top of the plugin file.
 * Is recommended to avoid the license notice when the plugin is published under the same license of pyLoad.


Plugin policy
-------------

...


Credits
-------

Refer to the attached file **CREDITS.md** for the extended credits.


Notes
-----

For news, wiki, forum and further info visit: <http://pyload.org/>.

To report bugs, suggest features, ask a question or help us out, visit: <https://github.com/pyload/pyload/issues>.
To request merging of an your patch or feature code, visit: <https://github.com/pyload/pyload/pr>.

Documentation about extending pyLoad can be found at <http://docs.pyload.org> or joining us at `#pyload` on `irc.freenode.net`.


-----------------------------------
###### pyLoad Team 2008-2015 ######
