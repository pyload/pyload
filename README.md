<p align="center"><a href="http://pyload.org/"><img src="/docs/resources/banner.png" alt="pyLoad" /></a></p>

[![Translation Status](http://translate.pyload.org/badges/pyload/localized.png "Translation Status")](http://translate.pyload.org/project/pyload/)

**pyLoad** is a Free and Open Source download manager written in Python and designed to be extremely lightweight.


Table of contents
-----------------

 - [Description](#description)
 - [Download](#download)
 - [Installation](#installation)
 - [Dependencies](#dependencies)
   - [Required](#required)
   - [Optional](#optional)
 - [Usage](#usage)
   - [First Start](#first-start)
   - [Web User Interface](#web-user-interface)
   - [Command Line Interface](#command-line-interface)
 - [Development](#development)
 - [Translations](#translations)
   - [Send a tip for translators](#send-a-tip-for-translators)
   - [Update templates](#update-templates)
   - [Retrieve PO files](#retrieve-po-files)
   - [Compile PO files](#compile-po-files)
 - [Licensing](#licensing)
   - [Main program](#main-program)
   - [Plugins](#plugins)
 - [Plugin policy](#plugin-policy)
 - [Credits](#credits)


Description
-----------

**pyLoad** was developed to run on any device able to connect to internet and supporting the Python programming language.
That's mean it's available for a really wide range of hardware platforms and operating systems.
You can control it entirely by web using its friendly Web User Interface.

All common video-sites, one-click-hosters, container formats and well known web standards are supported to allow you to download your files.
Additionaly, pyLoad has a great variety of plugins to automate common tasks and make unattended running possible.

pyLoad has a fully featured and well documented Application Programming Interface, easily extendable and accessible by external tools, cross-platform apps or other softwares.
Just take a look to the [Development section](#development) for more info about that.

For news, wiki, forum and further info visit the pyLoad website: <http://pyload.org/>.

Or joining us at `#pyload` on `irc.freenode.net`.


Download
--------

> **Note:**
> If you wanna use pyLoad on Windows, it's hightly recommented to install the latest **official** pre-build package for that platform.

Releases                                              | Download
----------------------------------------------------- | -----------------------------------------------------
Pre-build packages with changelog                     | <https://github.com/pyload/pyload/releases>

Pre-build packages are provided with all the software dependencies required to run pyLoad flawlessly on the referenced platform.
If you choose a source code, at least you need to have the proper Python version installed on your platform before launch pyLoad.

Source code                                           | Download
----------------------------------------------------- | -----------------------------------------------------
Latest stable version                                 | <https://github.com/pyload/pyload/archive/stable.zip>
Latest development version                            | <https://github.com/pyload/pyload/archive/master.zip>


Installation
------------

pyLoad currently works under:

 - [x] **Python 2.5**
 - [x] **Python 2.6**
 - [x] **Python 2.7**
 - [ ] Python 3
 - [ ] PyPy

You can install any missing software package from the *Python Package Index* typing:

    pip install <package-name>


Dependencies
------------

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
 - **Send2Trash**                                     *Trash support*
 - **colorlog**                                       *Colored log*
 - **bjoern** (<https://github.com/jonashaag/bjoern>) *More responsive web interface*
 - **node.js**                                        *ClickNLoad and other plugins*
   - or **ossp-js**
   - or **pyv8**
   - or **rhino**
   - or **spidermonkey**
 - **pyOpenSSL**                                      *SSL support*
 - **pycrypto**                                       *RSDF/CCF/DLC decrypting*
 - **simplejson**                                     *JSON speedup*
 - **tesseract**                                      *Captcha OCR support*


Usage
-----

### First Start ###

Run:

    python pyload.py

and follow the setup assistant instructions.

> **Note:**
> If you have installed pyLoad by a package-manager, command `python pyload.py` might be equivalent to `pyload`.

If something go wrong, you can restart the setup assistant typing:

    python pyload.py -s

Or you can even edit the configuration files located in your pyLoad home directory
(usually `%userprofile%/pyload` on Windows or `~/.pyload` otherwise) with your favorite editor.

For a short description of all the configuration options available visit: <http://pyload.org/configuration>.


### Web User Interface ###

Run:

    python pyload.py

So, to retrieve it point your browser to the socket address configured by setup (default to `http://localhost:8000`).

You can get a list of accepted arguments typing:

    python pyload.py -h


Development
-----------

 * pyLoad roadmap: <https://github.com/pyload/pyload/milestones>.
 * To report bugs, suggest features, ask for a question or help us out, visit: <https://github.com/pyload/pyload/issues>.
 * To request the merge of your code in the pyLoad repository, open a new *pull request* here: <https://github.com/pyload/pyload/pulls>.
 * Documentation about how extending pyLoad can be found at: <http://docs.pyload.org>.


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


### Update templates ###

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


Licensing
---------

### Main program  ###

Please refer to the attached [LICENSE.md](/LICENSE.md) for the extended license.


### Plugins  ###

According to the terms of the pyLoad license, official plugins must be treated as an extension of the main program
and released under the same license of pyLoad or a compatible one:

 * Any plugin published **without the \_\_license\_\_ attribute** is implied published under the same license of pyLoad.
 * Only plugins published **with a compatible license** will be accepted as official and included in the pyLoad repository.
 * **Un-official plugins are not supported**, so any issue report or feature request regarding this kind of plugin will be rejected.
 * Is recommended to put a **shorten** license notice only if nedfull to avoid misunderstandings about the adopted license.


Plugin policy
-------------

 - No cracking website or service
 - No drugs website or service
 - No e-commerce website or service
 - No government website or service
 - No illegal website or service in the country where its servers are located
 - No pedopornography website or service
 - No private website or service
 - No racist website or service
 - No warez website or service
 - No weapon website or service
 - ...


Credits
-------

Please refer to the attached [CREDITS.md](/CREDITS.md) for the extended credits.


-----------------------------------
###### pyLoad Team 2008-2015 ######
