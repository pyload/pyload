<p align="center"><a href="https://pyload.net/"><img src="/media/banner.png" alt="pyLoad" /></a></p>

**pyLoad** is a Free and Open Source download manager written in Python and designed to be
extremely lightweight, easily extensible and fully manageable via web.

_Continue reading about **pyLoad** amazing features on <https://pyload.net/>. ;)_


Table of contents
-----------------

- [Supported Platforms](#supported-platforms)
- [Dependencies](#dependencies)
  - [Supported Interpreters](#supported-interpreters)
  - [Required Packages](#required-packages)
  - [Optional Packages](#optional-packages)
  - [Test-suite Packages](#test-suite-packages)
- [Installation](#installation)
  - [PIP Install](#pip-install)
  - [Easy Install](#easy-install)
  - [Manually Install](#manually-install)
- [First Start](#first-start)
  - [Quick Start](#quick-start)
  - [Advanced Start](#advanced-start)
  - [Configuration](#configuration)
- [Usage](#usage)
  - [Basic Usage](#basic-usage)
  - [Script Usage](#script-usage)
- [Development](#development)
  - [Report an Issue](#report-an-issue)
  - [Submit a Code Contribution](#submit-a-code-contribution)
  - [~~Coding Guidelines~~](coding-guidelines)
  - [~~Localization~~](#localization)
  - [Performances](#performances)
 - [Licensing](#licensing)
  - [Main Program](#main-program)
  - [Plugins](#plugins)
 - [Credits](#credits)


Supported Platforms
-------------------

**pyLoad** runs under **Windows**, **MacOS** and Unix based systems like **Linux** and **FreeBSD**.

> **Note:**
> Currently **MacOS** and **BSD** platforms are NOT fully supported, some features may be unstable
> or missing.

> **Note:**
> Embedded platforms, proprietary NAS and routers systems are NOT officially supported,
> **pyLoad** may be crash unexpectately or NOT work at all under them!


Dependencies
------------

You need at least *Python 2.6* or *Python 3.3* to run **pyLoad**
and all of its [required software dependencies](#required-packages).

All the dependencies should be automatically installed by the [PIP install](#pip-install) procedure.
If you prefer the [Easy install](#easy-install) procedure, all the needed packages should be already
included in the [Pre-built Package](https://github.com/pyload/pyload/releases) you'll choose.

> **Note:**
> [Test-suite packages](#test-suite-packages) are required only if you want to test
> your installation with the built-in test suite.

### Supported Interpreters

- Python 1
  - [ ] CPython 1.0
  - [ ] CPython 1.5
  - [ ] CPython 1.6
- **Python 2**
  - [ ] CPython 2.0
  - [ ] CPython 2.1
  - [ ] CPython 2.2
  - [ ] CPython 2.3
  - [ ] CPython 2.4
  - [ ] ~~CPython 2.5~~ *(not supported anymore)*
  - [x] **CPython 2.6** *(supported but deprecated)*
  - [x] **CPython 2.7**
  - [ ] PyPy
- **Python 3**
  - [ ] CPython 3.0
  - [ ] CPython 3.1
  - [ ] CPython 3.2
  - [x] **CPython 3.3**
  - [x] **CPython 3.4**
  - [x] **CPython 3.5**
  - [x] **CPython 3.6**
  - [ ] PyPy3

### Required Packages

Package name | Min version | Notes
------------ | ----------- | ---------
argparse     | *           |
Beaker       | 1.6         |
bitmath      | *           |
bottle       | 0.10.0      |
colorama     | *           |
daemonize    | *           |
dbus-python  | *           | Unix only
future       | *           |
goslate      | *           |
psutil       | *           |
pycurl       | *           |
requests     | 2.0         |
ruamel.yaml  | *           |
Send2Trash   | *           |
setproctitle | *           |
tld          | *           |
validators   | *           |
watchdog     | *           |
wsgigzip     | *           |

### Optional Packages

Package name   | Min version | Purpose               | Notes
-------------- | ----------- | --------------------- | ---------
beautifulsoup4 | *           | Plugin dependencies   |
bjoern         | *           | Lightweight webserver | Unix only
colorlog       | *           | Colored log           |
Js2Py          | *           | JavaScript evaluation |
Pillow         | 2.0         | Captcha recognition   |
pip            | *           | pyLoad auto-update    |
pycrypto       | *           | Plugin dependencies   |
pyOpenSSL      | *           | SSL connection        |
unrar          | *           | Archive decompression |

### Test-suite Packages

Package name     | Min version | Notes
---------------- | ----------- | -----
nose             | *           |
requests         | 1.2.2       |
websocket-client | 0.8.0       |


Installation
------------

> **Note:**
> Before start, install **Python 2** (or **Python 3**) if missing.
> See <https://www.python.org/> to learn how to.

You can install **pyLoad** in several ways:
- [PIP install](#pip-install) *(recommended on Unix based systems)*
- [Easy install](#easy-install) *(recommended on Windows)*
- [Manually install](#manually-install)

### PIP Install

> **Note:**
> Before start, install **pip** if missing (and **setuptools** of course).
> See <https://pip.pypa.io/en/stable/installing/> to learn how to.

Type in your command shell ***with administrator/root privileges***:

    pip install pyload-ng

If the above command fails, try typing:

    pip install --user pyload-ng

If that fails too, try the [Easy Install](#easy-install) procedure
or at least the [Manually Install](#manually-install) procedure.

### Easy Install

  1. Download the [Pre-built Package](https://github.com/pyload/pyload/releases) for your platform.
  2. Extract the downloaded archive.
  3. Run *pyLoad* from the extracted archive path.

### Manually Install

  1. Get the latest tarball of the source code from the ~~[Stable Branch](https://github.com/pyload/pyload/archive/stable.zip) **OR** the [Testing Branch](https://github.com/pyload/pyload/archive/testing.zip)~~
     [Master Branch](https://github.com/pyload/pyload/archive/master.zip).
  2. Extract the downloaded archive.
  3. Change directory to the extracted archive path.
  4. Run the built-in setup utility as described in the [Configuration Section](#configuration).
  5. If setup fails or **pyLoad** crashes on startup,
     try manually installing the [software dependencies](#dependencies)
     or [report your issue](#report-an-issue).


First Start
-----------

### Quick Start

To run **pyLoad** with default profile, just type in your command shell:

    pyload

To run as daemon, type:

    pyload --daemon

To show the help list, type:

    pyload --help

_**That's all Folks!**_

> **Note:**
> Depending on your environment, command `pyload` might be equivalent to `pyLoad.py` or `pyLoad.exe`.

> **Note:**
> On first start, the setup assistant will be automatically launched to help you to configure
> your profile.

> **Note:**
> The web user interface will be accessible pointing your web browser to the ip address
> and configured port (defaults to `http://localhost:8010`).

> **Note:**
> The remote API server instead will be listening to `http://localhost:7447`.

### Advanced Start

To run **pyLoad** with a custom profile, type:

    pyload -p <profilename>

To run as daemon, type:

    pyload -p <profilename> --daemon

> **Note:**
> The `profile` argument must be a string name, **NOT a directory path**!

> **Note:**
> The `profile` argument is **optional**, but if you do not enter any value,
> the profile `default` will be used.
> **New profiles will be created automatically inside the current config directory when declared**.

### Configuration

After finishing the setup assistant **pyLoad** is ready to use and more configuration can be done
via the web user interface.
Additionally you could simply edit the config files located in your config directory.

To run the built-in setup utility, type:

    pyload setup

**OR** enter _(from the directory where **pyLoad** is installed)_:

    python setup.py install

> **Note:**
> The default path of the config directory is `%appdata%\pyload` on Windows platform
> and `~/.pyload` otherwise.

> **Note:**
> To learn how change the config directory see the help list.


Usage
-----

### Basic Usage

To start *pyLoad* in verbose (debug) mode, type:

    pyload --debug

To enable the webserver debugging as well, append:

    pyload --debug --webdebug

To stop a *pyLoad* instance, type:

    pyload stop -p <profilename>

**OR** directly, to stop anyone:

    pyload stop

To restart a **pyLoad** instance, type:

    pyload restart -p <profilename>

To update the **pyLoad** core (plugins excluded), type:

    pyload update

To run the built-in test suite, type:

    pyload test

### Script Usage

You can import **pyLoad** directly in your script:

    import pyload-ng as pyload

Available methods for the above `pyload` object are:

- `pyload.start(profile=None, configdir=None, refresh=0, remote=None, webui=None, debug=0,
  webdebug=0, daemon=False)`
  - **DESCRIPTION**: Start a process instance.
  - **RETURN**: Multiprocessing instance.
  - **ARGUMENTS**:
    - `profile` sets the profile name to use *(`default` if none entered)*.
    - `configdir` sets the config directory path to use *(`%appdata%\pyload` on Windows platforms
      or `~/.pyload` otherwise, if none entered)*.
    - `refresh` sets refresh/restore mode *(0=off|1=removes compiled and temp files|
      2=plus restore admin access `admin|pyload`)*.
    - `remote` enables remote API interface at entered *`IP address:Port number`
      (use defaults if none entered)*.
    - `webui` enables web user interface at entered *`IP address:Port number`
      (use defaults if none entered)*.
    - `debug` sets debug mode *(0=off|1=on|2=verbose)*.
    - `webdebug` sets webserver debugging *(0=off|1=on)*.
    - `daemon` daemonizes process.
- `pyload.stop(profile=None, wait=300)`
  - **DESCRIPTION**: Terminate a process instance.
  - **RETURN**: None type.
  - **ARGUMENTS**:
    - `profile` sets the profile name of the process to terminate
      *(terminate all the running processes if none entered)*.
    - `wait` sets the timeout *(in seconds)* before force to *kill* the process.
- `pyload.restart(profile=None, configdir=None, refresh=0, remote=None, webui=None, debug=0,
  webdebug=0, daemon=False)`
  - **DESCRIPTION**: Restart a process instance.
  - **RETURN**: Multiprocessing instance.
  - **ARGUMENTS**:
    - `profile` sets the profile name to use *(`default` if none entered)*.
    - `configdir` sets the config directory path to use *(`%appdata%\pyload` on Windows platforms
      or `~/.pyload` otherwise, if none entered)*.
    - `refresh` sets refresh/restore mode *(0=off|1=removes compiled and temp files|
      2=plus restore admin access `admin|pyload`)*.
    - `remote` enables remote API interface at entered *`IP address:Port number`
      (use defaults if none entered)*.
    - `webui` enables web user interface at entered *`IP address:Port number`
      (use defaults if none entered)*.
    - `debug` sets debug mode *(0=off|1=on|2=verbose)*.
    - `webdebug` sets webserver debugging *(0=off|1=on)*.
    - `daemon` daemonizes process.
- `pyload.setup()`
  - **DESCRIPTION**: Setup the package.
  - **RETURN**: None type.
  - **ARGUMENTS**: None.
- `pyload.update(dependencies=True, reinstall=False, prerelease=True)`
  - **DESCRIPTION**: Update the package.
  - **RETURN**: None type.
  - **ARGUMENTS**:
    - `dependencies` sets to update package dependencies.
    - `reinstall` sets to reinstall all packages even if they are already up-to-date.
    - `prerelease` sets to update to pre-release and development versions.
- `pyload.status(profile=None)`
  - **DESCRIPTION**: Show the process PID.
  - **RETURN**: PID list.
  - **ARGUMENTS**:
    - `profile` sets the profile name of the process to show *(show all the running processes
      if none entered)*.
- `pyload.info()`
  - **DESCRIPTION**: Show the package info.
  - **RETURN**: Info dict.
  - **ARGUMENTS**: None.
- `pyload.version()`
  - **DESCRIPTION**: Show the package version info.
  - **RETURN**: Version tuple.
  - **ARGUMENTS**: None.
- `pyload.test()`
  - **DESCRIPTION**: Run the test suite.
  - **RETURN**: None type.
  - **ARGUMENTS**: None.

> **Note:**
> `pyload.start` and `pyload.restart` return immediately, even if the resulting instance is
> not already fully running!

> **Note:**
> To stop a single **pyLoad** instance you MUST pass its profile name to the function `pyload.stop`,
> otherwise all the running instances of **pyLoad** will be terminated!

> **Note:**
> Calling function `pyload.restart` without a proper profile name will force to try to terminate
> the `default` profile one.

A quick example of how *start & stop* a couple instances of **pyLoad** launched concurrently:

    import pyload-ng as pyload
    pyload.start('myprofile1')
    pyload.start('MyProfile2')
    pyload.stop('myprofile1')
    pyload.stop('MyProfile2')


Development
-----------

- pyLoad repository: <https://github.com/pyload/pyload>.
- pyLoad documentation: <https://github.com/pyload/pyload/wiki>.
- pyLoad roadmap: <https://github.com/pyload/pyload/milestones>.

> **Note:**
> To report issues or submit your contributions, you need to be registered on *GitHub*.
> It's free and take less a minute to [signup](https://github.com/join).

### Report an Issue

To report an issue, suggest features, ask for a question or help us out,
[**open a ticket**](https://github.com/pyload/pyload/issues).

Please, always title your issues with a pertinent short description and expone accurately
the problem you encounter.

**Don't foget to attach a full debug log of your bugged session from the first start**
or we cannot help you.
To learn how to start **pyLoad** in *debug mode* see the [Usage Section](#usage).

### Submit a Code Contribution

To submit your code to the pyLoad repository
[**open a new _Pull Request_**](https://github.com/pyload/pyload/pulls).

You have to sign our [Contributor License Agreement](/CLA.md) to allow us to integrate your work
in the pyLoad repository.
You can sign it easily from within your pull request itself.

For further information see the [License Section](#license).

### Coding Guidelines

> **Notice:**
> **Coding Guidelines not yet available.**

### Localization

> **Notice:**
> **Localization not yet available.**

> **Note:**
> The localization process is managed directly under the *Crowdin* page
> <http://crowdin.net/project/pyload>.

You can download the latest locale files from ~~<https://crowdin.com/download/project/pyload.zip>~~.

To compile them, run the built-in setup utility *(see the [Configuration Section](#configuration))*.

### Performances

No stats right now. :(


Licensing
---------

### Main Program

Please refer to the included [LICENSE](/LICENSE.md) for the extended license and CLA.

### Plugins

Please refer to the plugins [LICENSE](https://github.com/pyload/plugins/blob/master/README.md)
for the extended license.


Credits
-------

Please refer to the included [CREDITS](/CREDITS.md) for the extended credits.


--------------------------------
###### (c) 2009-2017 pyLoad Team
