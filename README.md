<p align="center"><a href="https://pyload.net"><img src="/media/banner.png" alt="pyLoad" /></a></p>

**pyLoad** is the Free and Open Source download manager written in Pure Python
and designed to be extremely lightweight, fully customizable and remotely
manageable.

> **Notice:**
> **[Master Branch](https://github.com/pyload/pyload/tree/master)
> is under heavy development, very unstable, often broken.**

> **Notice:**
> **[Stable Branch](https://github.com/pyload/pyload/tree/stable) is production
> ready**.

**Status**:

[![Travis Build Status](https://travis-ci.org/pyload/pyload.svg?branch=master)](https://travis-ci.org/pyload/pyload)
[![AppVeyor Build status](https://ci.appveyor.com/api/projects/status/86d5f83kmw6soyfq/branch/master?svg=true)](https://ci.appveyor.com/project/vuolter/pyload/branch/master)
[![Requirements Status](https://requires.io/github/pyload/pyload/requirements.svg?branch=master)](https://requires.io/github/pyload/pyload/requirements/?branch=master)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/240a2201eee54680b1c34bf86a32abd0)](https://www.codacy.com/app/pyLoad/pyload?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=pyload/pyload&amp;utm_campaign=Badge_Grade)
[![Scrutinizer Code Quality](https://scrutinizer-ci.com/g/pyload/pyload/badges/quality-score.png?b=master)](https://scrutinizer-ci.com/g/pyload/pyload/?branch=master)
[![PyPI Status](https://img.shields.io/pypi/status/pyload.core.svg)](https://pypi.python.org/pypi/pyload.core)
[![PyPI Version](https://img.shields.io/pypi/v/pyload.core.svg)](https://pypi.python.org/pypi/pyload.core)
[![PyPI Python Versions](https://img.shields.io/pypi/pyversions/pyload.core.svg)](https://pypi.python.org/pypi/pyload.core)

**Licensing**:

[![CLA assistant](https://cla-assistant.io/readme/badge/pyload/pyload)](https://cla-assistant.io/pyload/pyload)
[![PyPI License](https://img.shields.io/pypi/l/pyload.core.svg)](https://pypi.python.org/pypi/pyload.core)

**Contacts**:

[![pyload.net](https://img.shields.io/badge/.net-pyload-orange.svg)](https://pyload.net)
[![Twitter](https://img.shields.io/badge/-twitter-429cd6.svg?logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2CPD94bWwgdmVyc2lvbj0iMS4wIiA%2FPjwhRE9DVFlQRSBzdmcgIFBVQkxJQyAnLS8vVzNDLy9EVEQgU1ZHIDEuMC8vRU4nICAnaHR0cDovL3d3dy53My5vcmcvVFIvMjAwMS9SRUMtU1ZHLTIwMDEwOTA0L0RURC9zdmcxMC5kdGQnPjxzdmcgZW5hYmxlLWJhY2tncm91bmQ9Im5ldyAwIDAgMzIgMzIiIGhlaWdodD0iMzJweCIgaWQ9IkxheWVyXzEiIHZlcnNpb249IjEuMCIgdmlld0JveD0iMCAwIDMyIDMyIiB3aWR0aD0iMzJweCIgeG1sOnNwYWNlPSJwcmVzZXJ2ZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIiB4bWxuczp4bGluaz0iaHR0cDovL3d3dy53My5vcmcvMTk5OS94bGluayI%2BPHBhdGggZD0iTTMxLjk5Myw2LjA3N0MzMC44MTYsNi42LDI5LjU1Miw2Ljk1MywyOC4yMjMsNy4xMWMxLjM1NS0wLjgxMiwyLjM5Ni0yLjA5OCwyLjg4Ny0zLjYzICBjLTEuMjY5LDAuNzUxLTIuNjczLDEuMjk5LTQuMTY4LDEuNTkyQzI1Ljc0NCwzLjc5NywyNC4wMzgsMywyMi4xNDksM2MtMy42MjUsMC02LjU2MiwyLjkzOC02LjU2Miw2LjU2MyAgYzAsMC41MTQsMC4wNTcsMS4wMTYsMC4xNjksMS40OTZDMTAuMzAxLDEwLjc4NSw1LjQ2NSw4LjE3MiwyLjIyNyw0LjIwMWMtMC41NjQsMC45Ny0wLjg4OCwyLjA5Ny0wLjg4OCwzLjMgIGMwLDIuMjc4LDEuMTU5LDQuMjg2LDIuOTE5LDUuNDY0Yy0xLjA3NS0wLjAzNS0yLjA4Ny0wLjMyOS0yLjk3Mi0wLjgyMWMtMC4wMDEsMC4wMjctMC4wMDEsMC4wNTYtMC4wMDEsMC4wODIgIGMwLDMuMTgxLDIuMjYyLDUuODM0LDUuMjY1LDYuNDM3Yy0wLjU1LDAuMTQ5LTEuMTMsMC4yMy0xLjcyOSwwLjIzYy0wLjQyNCwwLTAuODM0LTAuMDQxLTEuMjM0LTAuMTE3ICBjMC44MzQsMi42MDYsMy4yNTksNC41MDQsNi4xMyw0LjU1OGMtMi4yNDUsMS43Ni01LjA3NSwyLjgxMS04LjE1LDIuODExYy0wLjUzLDAtMS4wNTMtMC4wMzEtMS41NjYtMC4wOTIgIEMyLjkwNSwyNy45MTMsNi4zNTUsMjksMTAuMDYyLDI5YzEyLjA3MiwwLDE4LjY3NS0xMC4wMDEsMTguNjc1LTE4LjY3NWMwLTAuMjg0LTAuMDA4LTAuNTY4LTAuMDItMC44NSAgQzMwLDguNTUsMzEuMTEyLDcuMzk1LDMxLjk5Myw2LjA3N3oiIGZpbGw9IiM1NUFDRUUiLz48Zy8%2BPGcvPjxnLz48Zy8%2BPGcvPjxnLz48L3N2Zz4%3D)](https://twitter.com/pyload)
[![Facebook](https://img.shields.io/badge/-facebook-3a589e.svg?logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2CPD94bWwgdmVyc2lvbj0iMS4wIiA%2FPjwhRE9DVFlQRSBzdmcgIFBVQkxJQyAnLS8vVzNDLy9EVEQgU1ZHIDEuMC8vRU4nICAnaHR0cDovL3d3dy53My5vcmcvVFIvMjAwMS9SRUMtU1ZHLTIwMDEwOTA0L0RURC9zdmcxMC5kdGQnPjxzdmcgZW5hYmxlLWJhY2tncm91bmQ9Im5ldyAwIDAgMzIgMzIiIGhlaWdodD0iMzJweCIgaWQ9IkxheWVyXzEiIHZlcnNpb249IjEuMCIgdmlld0JveD0iMCAwIDMyIDMyIiB3aWR0aD0iMzJweCIgeG1sOnNwYWNlPSJwcmVzZXJ2ZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIiB4bWxuczp4bGluaz0iaHR0cDovL3d3dy53My5vcmcvMTk5OS94bGluayI%2BPGc%2BPHBhdGggZD0iTTMyLDMwYzAsMS4xMDQtMC44OTYsMi0yLDJIMmMtMS4xMDQsMC0yLTAuODk2LTItMlYyYzAtMS4xMDQsMC44OTYtMiwyLTJoMjhjMS4xMDQsMCwyLDAuODk2LDIsMlYzMHoiIGZpbGw9IiMzQjU5OTgiLz48cGF0aCBkPSJNMjIsMzJWMjBoNGwxLTVoLTV2LTJjMC0yLDEuMDAyLTMsMy0zaDJWNWMtMSwwLTIuMjQsMC00LDBjLTMuNjc1LDAtNiwyLjg4MS02LDd2M2gtNHY1aDR2MTJIMjJ6IiBmaWxsPSIjRkZGRkZGIiBpZD0iZiIvPjwvZz48Zy8%2BPGcvPjxnLz48Zy8%2BPGcvPjxnLz48L3N2Zz4%3D)](https://www.facebook.com/pyload)
[![Join the chat](https://badges.gitter.im/pyload/pyload.svg)](https://gitter.im/pyload/pyload?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
[![IRC Freenode](https://img.shields.io/badge/irc-freenode-lightgray.svg)](https://kiwiirc.com/client/irc.freenode.com/#pyload)


Table of contents
-----------------

- [Supported Platforms](#supported-platforms)
- [Supported Interpreters](#supported-interpreters)
- [Installation](#installation)
  - [Dependencies](#dependencies)
  - [PIP Install](#pip-install)
  - [Tarball Install](#tarball-install)
- [Usage](#usage)
  - [Quick Start](#quick-start)
  - [Advanced Options](#advanced-options)
  - [Script Usage](#script-usage)
- [Development](#development)
  - [Report an Issue](#report-an-issue)
  - [Submit a Code Contribution](#submit-a-code-contribution)
  - [Coding Guidelines](#coding-guidelines)
  - [~~Localization~~](#localization)
  - [~~Performances~~](#performances)
- [Licensing](#licensing)
  - [Open Source License](#open-source-license)
  - [Alternative License](#alternative-license)
  - [Contributor License Agreement](#contributor-license-agreement)
- [Credits](#credits)
- [Release History](#release-history)


Supported Platforms
-------------------

**pyLoad** works with **Windows**, **MacOS** and Unix based systems like
**Linux** and **FreeBSD**.

Embedded platforms, proprietary NAS and routers systems are NOT officially
supported, **pyLoad** may crash unexpectately or NOT work at all under them!

> **Note:**
> Currently, **MacOS** and **BSD** platforms are NOT fully supported,
> some features may be missing or unstable.


Supported Interpreters
----------------------

To run **pyLoad** you must have installed on your system the
[Python interpreter](https://www.python.org).

You need at least `Python2.6` or `Python3.3` to run **pyLoad**.
Python versions from `Python3.0` to `Python3.2` are NOT supported!

An **experimental support** for [PyPy](http://pypy.org) is available;
as expected you need at least `PyPy2.6` or `PyPy3.3` to run **pyLoad**.


Installation
------------

You can install **pyLoad** in several ways:
- [PIP install](#pip-install) _(recommended on Unix based systems)_
- [Tarball Install](#tarball-install)

### Dependencies

Please refer to
https://requires.io/github/pyload/pyload/requirements/?branch=master
for the package dependencies list.

All entries are mandatory _for the own scope_:

- Packages listed in `setup.txt` are required by the built-in `setup.py` to
**run itself**.
- Packages listed in `install.txt` are required by the built-in `setup.py` just
to **install** the pyLoad package.
- Packages listed in `test.txt` are required by the built-in `setup.py` just to
**test** the pyLoad package.

> **Note:**
> All the mandatory dependencies should be solved automatically if you choose
> the [PIP install method](#pip-install).

> **Note:**
> To install **pyLoad** using the [PIP install method](#pip-install) you need
> the package [pip](https://pypi.python.org/pypi/pip), **version 7 or later**.
> To learn how to install it see <https://pip.pypa.io/en/stable/installing/>.

### PIP Install

Type in your command shell **with _administrator/root_ privileges**:

    pip install pyload.core[full]

Under Unix based systems this usually means you have to use `sudo`:

    sudo pip install pyload.core[full]

The `full` option ensures that all the optional packages will downloaded and
installed as well as the mandatory ones.

You can install just the essential dependencies typing:

    pip install pyload.core

If the above commands fail, consider using the
[`--user`](https://pip.pypa.io/en/latest/user_guide/#user-installs) option:

    pip install --user pyload.core

If this command fails too, try the [others install methods](#installation).
Leaves as last resort to [report your issue](#report-an-issue).

### Tarball Install

1. Get the latest _tarball_ of the source code in format
[ZIP](https://github.com/pyload/pyload/archive/master.zip) or
[TAR](https://github.com/pyload/pyload/archive/master.tar.gz).
2. Extract the downloaded archive.
3. From the extracted directory path, run the command
`python setup.py build`.
4. Then run the command `python setup.py install`.


Usage
-----

### Quick Start

To run **pyLoad** with the default profile, just type in your command shell:

    pyload

To run as daemon, type:

    pyload --daemon

To run in _debug mode_, type:

    pyload --debug

To show the help list, type:

    pyload --help

> **Note:**
> Depending on your environment, command `pyload` might be equivalent to
> `pyLoad.py` or `pyLoad.exe`.

> **Note:**
> If you have installed the package `pyload.webui`, the web user interface is
reachable pointing your web browser to the configured ip address and port
(default to `http://localhost:8010`).

> **Note:**
> If you have installed the package `pyload.rpc`, the remote API server is
listening to the configured ip address and port
(default to `http://localhost:7447`).

### Advanced Options

**pyLoad**'s command line supports several options:
`start`, `stop`, `restart`, `version`.

> **Note:**
> If you do not enter any option, `start` will be used.

To run **pyLoad** with a custom profile, type:

    pyload start --profile <profilename>

Omitting the `start` option:

    pyload --profile <profilename>

Shorten:

    pyload -p <profilename>

> **Note:**
> `<profilename>` must be a plain text string, **NOT a directory path**!

> **Note:**
> If you do not enter any `<profilename>`, the string `default` will be used.

To run **pyLoad** with a custom config folder:

    pyload start --configdir <dirpath>

Omitting the `start` option:

    pyload --configdir <dirpath>

Shorten:

    pyload -c <dirpath>

> **Note:**
> If you do not enter any `<dirpath>`, the path `%appdata%\pyload` will be
> choosed for Windows platforms and `~/.pyload` otherwise.

> **Notice:**
> **When a new profile is declared, a directory with the same name is created
> inside the config directory.**

To **quit** a pyLoad instance, type:

    pyload quit --profile <profilename>

To **restart** a pyLoad instance, type:

    pyload restart --profile <profilename>

### Script Usage

To import **pyLoad** in your script, enter:

    import pyload.core

Available methods:

- `pyload.core.start(profile=None, configdir=None, refresh=0, remote=None, webui=None, debug=0,
  webdebug=0, daemon=False)`
  - **DESCRIPTION**: Start a process instance.
  - **RETURN**: Multiprocessing instance.
  - **ARGUMENTS**:
   - `profile` sets the profile name to use *(`default` if none entered)*.
   - `configdir` sets the config directory path to use *(`%appdata%\pyload` on Windows platforms
     or `~/.pyload` otherwise, if none entered)*.
   - `refresh` sets refresh/restore mode *(0=off; 1=removes compiled and temp files;
     2=plus restore default username `admin` and password `pyload`)*.
   - `remote` enables remote API interface at entered *`IP address:Port number`
     (use defaults if none entered)*.
   - `webui` enables web user interface at entered *`IP address:Port number`
     (use defaults if none entered)*.
   - `debug` sets debug mode *(0=off; 1=on; 2=verbose)*.
   - `webdebug` sets webserver debugging *(0=off; 1=on)*.
   - `daemon` daemonizes process.
- `pyload.core.quit(profile=None, wait=300)`
  - **DESCRIPTION**: Terminate a process instance.
  - **RETURN**: None type.
  - **ARGUMENTS**:
    - `profile` sets the profile name of the process to terminate
      *(terminate all the running processes if none entered)*.
    - `wait` sets the timeout (in seconds) before force to *kill* the process.
- `pyload.core.restart(profile=None, configdir=None, refresh=0, remote=None, webui=None, debug=0,
  webdebug=0, daemon=False)`
  - **DESCRIPTION**: Restart a process instance.
  - **RETURN**: Multiprocessing instance.
  - **ARGUMENTS**:
    - `profile` sets the profile name to use *(`default` if none entered)*.
    - `configdir` sets the config directory path to use *(`%appdata%\pyload` on Windows platforms
      or `~/.pyload` otherwise, if none entered)*.
    - `refresh` sets refresh/restore mode *(0=off; 1=removes compiled and temp files;
      2=plus restore default username `admin` and password `pyload`)*.
    - `remote` enables remote API interface at entered *`IP address:Port number`
      (use defaults if none entered)*.
    - `webui` enables web user interface at entered *`IP address:Port number`
      (use defaults if none entered)*.
    - `debug` sets debug mode *(0=off; 1=on; 2=verbose)*.
    - `webdebug` sets webserver debugging *(0=off; 1=on)*.
    - `daemon` daemonizes process.
- ~~`pyload.core.setup()`~~
  - **DESCRIPTION**: Setup the package.
  - **RETURN**: None type.
  - **ARGUMENTS**: None.
- ~~`pyload.core.upgrade(dependencies=True, reinstall=False, prerelease=True)`~~
  - **DESCRIPTION**: Update the package.
  - **RETURN**: None type.
  - **ARGUMENTS**:
    - `dependencies` sets to update package dependencies.
    - `reinstall` sets to reinstall all packages even if they are already up-to-date.
    - `prerelease` sets to update to pre-release and development versions.
- `pyload.core.status(profile=None)`
  - **DESCRIPTION**: Show the process PID.
  - **RETURN**: PID list.
  - **ARGUMENTS**:
    - `profile` sets the profile name of the process to show *(show all the
      running processes if none entered)*.
- ~~`pyload.core.info()`~~
  - **DESCRIPTION**: Show the package info.
  - **RETURN**: Info dict.
  - **ARGUMENTS**: None.
- `pyload.core.version()`
  - **DESCRIPTION**: Show the package version info.
  - **RETURN**: Version tuple.
  - **ARGUMENTS**: None.
- ~~`pyload.core.test()`~~
  - **DESCRIPTION**: Run the test suite.
  - **RETURN**: None type.
  - **ARGUMENTS**: None.

> **Note:**
> `pyload.core.start` and `pyload.core.restart` return immediately, even if the
> resulting instance is not already fully running!

> **Note:**
> To terminate a single pyLoad instance you MUST pass its profile name to the
> function `pyload.core.quit`, otherwise all the running instances of **pyLoad**
> will be terminated!

> **Note:**
> Calling function `pyload.core.restart` without a proper profile name will
> force to try to terminate the `default` profile one.

A quick example of how *start & stop* a couple instances of **pyLoad** launched
concurrently:

    import pyload
    pyload.core.start('myprofile1')
    pyload.core.start('MyProfile2')
    pyload.core.quit('myprofile1')
    pyload.core.quit('MyProfile2')


Development
-----------

- pyLoad repository: <https://github.com/pyload/pyload>.
- pyLoad documentation: <https://github.com/pyload/pyload/wiki>.
- pyLoad roadmap: <https://github.com/pyload/pyload/milestones>.

> **Note:**
> To report issues or submit your contributions, you need to be registered
> on *GitHub*. It's free and take less a minute to
> [signup](https://github.com/join).

### Report an Issue

To report an issue, suggest features, ask for a question or help us out,
[**open a ticket**](https://github.com/pyload/pyload/issues).

Please, always title your issues with a pertinent short description and expone
accurately the problem you encounter.

**Don't foget to attach a full debug log of your bugged session from the
first start** or we cannot help you.

> **Note:**
> To learn how to start **pyLoad** in *debug mode* see the
> [Usage Section](#usage).

### Submit a Code Contribution

To submit your code to the pyLoad repository
[**open a new _Pull Request_**](https://github.com/pyload/pyload/pulls).

If you want to contribute to the project you have to sign our
[Contributor License Agreement](#contributor-license-agreement) to allow us
to integrate your work in the official repository.
You can sign it easily from within your pull request itself.

For further information see the [License Section](#license).

### Coding Guidelines

Please, follow the
[PEP 8 - Style Guide for Python Code](https://www.python.org/dev/peps/pep-0008/).

### Localization

> **Notice:**
> **Localization not yet available.**

You can download the latest locale files from
~~<https://crowdin.com/download/project/pyload.zip>~~.

### Performances

> **Notice:**
> **Stats not yet available.**


Licensing
---------

### Open Source License

You are allowed to use this software under the terms of the **GNU Affero
General Public License** as published by the Free Software Foundation;
either **version 3** of the License, or (at your option) any later version.

Please refer to the included [LICENSE](/LICENSE.md) for the extended
_Open Source License_.

### Alternative License

With an explicit permission of the authors you may use or distribute
this software under a different license according to the agreement.

Contact us at licensing@pyload.net for any question about our code licensing.

### Contributor License Agreement

Please refer to the included [CLA](/CLA.md) for the extended agreement.

However, to summarise, this is essentially what you will be agreeing to:

- You affirm that you have the right to provide the contribution
(i.e. it's your own work).
- You grant the project a perpetual, non-exclusive license to use the
contribution.
- You grant the project rights to change the outbound license that we use to
distribute the code.
- You retain full ownership (copyright) of your submission and are free to do
with it as you please.

Please contact us at cla@pyload.net if you wish to contribute to the project,
but feel you cannot sign the agreement.


Credits
-------

Please refer to the included [CREDITS](/CREDITS.md) for the extended credits.


Release History
---------------

Please refer to the included [CHANGELOG](/CHANGELOG.md) for the detailed release
history.


-----------------------------------------------------
###### © 2015-2017 Walter Purcaro <vuolter@gmail.com>
###### © 2009-2015 pyLoad Team
