<p align="center"><a href="https://pyload.net/"><img src="/media/banner.png" alt="pyLoad" /></a></p>

**pyLoad** is a Free and Open Source download manager written in Python and designed to be extremely lightweight,
easily extensible and fully manageable via web.

*Continue reading about **pyLoad** amazing features on <https://pyload.net/>. ;)*


Table of contents
-----------------

 - [Supported Platforms](#supported-platforms)
 - [Dependencies](#dependencies)
    - [Tested Interpreters](#tested-interpreters)
    - [Required Packages](#required-packages)
    - [Optional Packages](#optional-packages)
 - [Installation](#installation)
    - [PIP Install](#pip-install)
    - [Manually Install](#manually-install)
    - [Sources Install](#sources-install)
 - [Quick Start](#quick-start)
 - [Advanced Start](#advanced-start)
 - [Configuration](#configuration)
 - [Advanced Usage](#advanced-usage)
 - [Script Usage](#script-usage)
 - [Performances](#performances)
 - [Development](#development)
 - [Localization](#localization)
 - [Licensing](#licensing)
   - [Main Program](#main-program)
   - [Plugins](#plugins)
 - [Credits](#credits)


Supported Platforms
-------------------

**pyLoad** runs under **Windows**, **MacOS** and Unix based systems like **Linux** and **FreeBSD**.

> **Note:**
> Currently **MacOS** and **BSD** platforms are NOT fully supported, some features may be unstable or missing.

> **Note:**
> Embedded platforms, proprietary NAS and routers systems are NOT officially supported, **pyLoad** may be crash unexpectately or NOT work at all under them!


Dependencies
------------

You need at least *Python 2.6* or *Python 3.4* to run **pyLoad** and all of its required software dependencies.
All the dependencies should be automatically installed if you choose the [PIP install procedure](#pip-install).
The **pre-built packages** also install all the needed dependencies or have them included.
So, it's not recommended to install the dependencies manually.

### Tested Interpreters

  - **Python 2**
    - [ ] CPython 2.0
    - [ ] CPython 2.1
    - [ ] CPython 2.2
    - [ ] CPython 2.3
    - [ ] CPython 2.4
    - [ ] CPython 2.5 *(not supported anymore)*
    - [x] **CPython 2.6** *(supported but deprecated)*
    - [x] **CPython 2.7**
    - [ ] PyPy
  - **Python 3**
    - [ ] CPython 3.0
    - [ ] CPython 3.1
    - [ ] CPython 3.2
    - [ ] CPython 3.3
    - [x] **CPython 3.4**
    - [x] **CPython 3.5**
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


Installation
------------

> **Note:**
> Before start, install **Python 2** (or **Python 3**) if missing. See <https://www.python.org/> to learn how to.

You can install **pyLoad** in several ways:
  - [PIP install](#pip-install) *(recommended)*
  - [Manually install](#manually-install)
  - [Sources install](#sorces-install)

### PIP Install

> **Note:**
> Before start, install **pip** if missing (and **setuptools** of course). See <https://pip.pypa.io/en/stable/installing/> to learn how to.

Type in your command shell ***with administrator/root privileges***:

    pip install pyload-ng

If the above command fails, try typing:

    pip install --user pyload-ng

### Manually Install

  1. Download the **pre-built packages** for your platform from <https://github.com/pyload/pyload/releases>.
  2. Extract the downloaded archive.
  3. Change directory to the extracted archive path.
  4. Run the built-in setup utility, typing in your command shell: `python setup.py install`.

### Sources Install

  1. Get the latest tarball of the source code from <https://github.com/pyload/pyload/archive/stable.zip> *(stable)* **OR** <https://github.com/pyload/pyload/archive/testing.zip> *(testing)*.
  2. Extract the downloaded archive.
  3. Change directory to the extracted archive path.
  4. Run the built-in setup utility, typing in your command shell: `python setup.py install`.
  5. If setup fails or **pyLoad** crashes, manually install the [Required software dependencies](#required-packages) at least and retry.


Quick Start
-----------

To run **pyLoad** with default profile, just type in your command shell:

    pyload

To run as daemon, type:

    pyload --daemon

To show the help list, type:

    pyload --help

*That's all Folks!*

> **Note:**
> Depending on your environment, command `pyload` might be equivalent to `pyLoad.py` or `pyLoad.exe`.

> **Note:**
> On first start, the setup assistant will be automatically launched to help you to configure your profile.

> **Note:**
> The web user interface will be accessible pointing your web browser to the ip address and configured port (defaults to `http://localhost:8010`).

> **Note:**
> The remote API server instead will be listening on `http://localhost:7447`.


Advanced Start
--------------

To run **pyLoad** with a custom profile, type:

    pyload -p <profilename>

To run as daemon, type:

    pyload -p <profilename> --daemon

> **Note:**
> The `profile` argument must be a string name, **NOT a directory path**!

> **Note:**
> The `profile` argument is **optional**, but if you do not enter any value, the profile `default` will be used.
> **New profiles will be created automatically inside the current config directory when declared**.


Configuration
-------------

After finishing the setup assistant **pyLoad** is ready to use and more configuration can be done via the web user interface.
Additionally you could simply edit the config files located in your config directory.

To run the built-in setup utility, type:

    pyload setup

**Or** type *(from the directory where **pyLoad** is installed)*:

    python pyLoad.py setup.py

> **Note:**
> The default path of the config directory is `%appdata%\pyload` on Windows platform and `~/.pyload` otherwise.

> **Note:**
> To learn how change the config directory see the help list.


Advanced Usage
--------------

To start *pyLoad* in verbose (debug) mode, type:

    pyload --debug

To enable the webserver debugging as well, append:

    pyload --debug --webdebug

To stop a *pyLoad* instance, type:

    pyload stop -p <profilename>

**Or** directly, to stop anyone:

    pyload stop

To restart a **pyLoad** instance, type:

    pyload restart -p <profilename>

To update the **pyLoad** core (NOT plugins), type:

    pyload update

To run the built-in test suite, type:

    pyload test


Script Usage
------------

You can import **pyLoad** directly in your script in this way:

    import pyload-ng as pyload

Available methods of the `pyload` object are:

  - `pyload.start(profile=None, configdir=None, refresh=0, remote=None, webui=None, debug=0, webdebug=0, daemon=False)`
    - **DESCRIPTION**: Start a process instance.
    - **RETURN**: Multiprocessing instance.
    - `profile` sets the profile name to use *(`default` if none entered)*.
    - `configdir` sets the config directory path to use *(`%appdata%\pyload` on Windows platforms or `~/.pyload` otherwise, if none entered)*.
    - `refresh` sets refresh/restore mode *(0=off|1=removes compiled and temp files|2=plus restore admin access `admin|pyload`)*.
    - `remote` enables remote API interface at entered *`IP address:Port number` (use defaults if none entered)*.
    - `webui` enables web user interface at entered *`IP address:Port number` (use defaults if none entered)*.
    - `debug` sets debug mode *(0=off|1=on|2=verbose)*.
    - `webdebug` sets webserver debugging *(0=off|1=on)*.
    - `daemon` daemonizes process.
  - `pyload.stop(profile=None, wait=300)`
    - **DESCRIPTION**: Terminate a process instance.
    - **RETURN**: None type.
    - `profile` sets the profile name of the process to terminate *(terminate all the running processes if none entered)*.
    - `wait` sets the timeout *(in seconds)* before force to *kill* the process.
  - `pyload.restart(profile=None, configdir=None, refresh=0, remote=None, webui=None, debug=0, webdebug=0, daemon=False)`
    - **DESCRIPTION**: Restart a process instance.
    - **RETURN**: Multiprocessing instance.
    - `profile` sets the profile name to use *(`default` if none entered)*.
    - `configdir` sets the config directory path to use *(`%appdata%\pyload` on Windows platforms or `~/.pyload` otherwise, if none entered)*.
    - `refresh` sets refresh/restore mode *(0=off|1=removes compiled and temp files|2=plus restore admin access `admin|pyload`)*.
    - `remote` enables remote API interface at entered *`IP address:Port number` (use defaults if none entered)*.
    - `webui` enables web user interface at entered *`IP address:Port number` (use defaults if none entered)*.
    - `debug` sets debug mode *(0=off|1=on|2=verbose)*.
    - `webdebug` sets webserver debugging *(0=off|1=on)*.
    - `daemon` daemonizes process.
  - `pyload.setup()`
    - **DESCRIPTION**: Setup the package.
    - **RETURN**: None type.
  - `pyload.update(dependencies=True, reinstall=False, prerelease=True)`
    - **DESCRIPTION**: Update the package.
    - **RETURN**: None type.
    - `dependencies` sets to update package dependencies.
    - `reinstall`sets to reinstall all packages even if they are already up-to-date.
    - `prerelease`sets to update to pre-release and development versions.
  - `pyload.status(profile=None)`
    - **DESCRIPTION**: Show the process PID.
    - **RETURN**: PID list.
    - `profile` sets the profile name of the process to show *(show all the running processes if none entered)*.
  - `pyload.info()`
    - **DESCRIPTION**: Show the package info.
    - **RETURN**: Info dict.
  - `pyload.version()`
    - **DESCRIPTION**: Show the package version info.
    - **RETURN**: Version tuple.
  - `pyload.test()`
    - **DESCRIPTION**: Run the test suite.
    - **RETURN**: None type.

> **Note:**
> `pyload.start` (and `pyload.restart`) returns immediately, even if the resulting instance is not fully running already!

> **Note:**
> To stop a single **pyLoad** instance you MUST pass its profile name to the function `pyload.stop`,
> otherwise all the running instances of **pyLoad** will be terminated!

> **Note:**
> Calling function `pyload.restart` without a proper profile name will force to try to terminate the `default` profile one.

A quick example of how *start & stop* a couple instances of **pyLoad** launched concurrently:

    import pyload-ng as pyload
    pyload.start('myprofile1')
    pyload.start('MyProfile2')
    pyload.stop('myprofile1')
    pyload.stop('MyProfile2')


Performances
------------

No stats right now.


Development
-----------

  - **pyLoad** documentation: <https://github.com/pyload/pyload/wiki>.
  - **pyLoad** roadmap: <https://github.com/pyload/pyload/milestones>.
  - To report bugs, suggest features, ask for a question or help us out, visit: <https://github.com/pyload/pyload/issues>.
  - To submit your code to the **pyLoad** repository, open a new *Pull Request* here: <https://github.com/pyload/pyload/pulls>.


Localization
------------

> **Note:**
> The localization process is managed with **Crowdin** here: <http://crowdin.net/project/pyload>.

You can download the latest locale files from <https://crowdin.com/download/project/pyload.zip>.
To compile them, run the built-in setup utility *(see the [Configuration section](#configuration))*.


Licensing
---------

### Main Program

Please refer to the included [LICENSE](/LICENSE.md) for the extended license.

### Plugins

Please refer to the included [PLUGIN LICENSE](https://github.com/pyload/plugins/readme.md) for the extended license.


Credits
-------

Please refer to the included [CREDITS](/CREDITS.md) for the extended credits.


----------------------------------
###### © 2009-2017 The pyLoad Team
