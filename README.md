<br />
<p align="center">
  <img src="https://raw.githubusercontent.com/pyload/pyload/main/media/banner.png" alt="pyLoad" height="110" />
</p>
<h2 align="center">The free and open-source Download Manager written in pure Python</h2>
<h4 align="center">
  <img alt="status" src="https://img.shields.io/pypi/status/pyload-ng?style=flat-square">
  <a href="https://github.com/pyload/pyload/actions">
    <img alt="build" src="https://img.shields.io/github/actions/workflow/status/pyload/pyload/test.yml?event=push&style=flat-square">
  </a>
  <a href="https://www.codacy.com/gh/pyload/pyload">
    <img alt="codacy" src="https://img.shields.io/codacy/grade/1d047f77c0a6496eb708e1b3ca83006b?label=grade&style=flat-square">
  </a>
  <img alt="python" src="https://img.shields.io/pypi/pyversions/pyload-ng?style=flat-square">
  <a href="https://pypi.python.org/pypi/pyload-ng">
    <img alt="pypi" src="https://img.shields.io/pypi/v/pyload-ng?style=flat-square">
  </a>
  <a href="https://pyup.io/repos/github/pyload/pyload">
    <img alt="pyup" src="https://pyup.io/repos/github/pyload/pyload/shield.svg">
  </a>
</h4>

<br />
<br />

## Choose your Version

**The newest version of pyLoad** running on Python 3.6+ and PyPy (experimental) is developed in the [main branch on GitHub](https://github.com/pyload/pyload/tree/main) and published as [pyload-ng on PyPI](https://pypi.org/project/pyload-ng/).

**The old version of pyLoad** working on Python 2 is still available in the [stable branch on GitHub](https://github.com/pyload/pyload/tree/stable), pre-built packages are available for download on the [releases page on GitHub](https://github.com/pyload/pyload/releases).

This README covers only the latest version of pyLoad.

## Quick Start

Open a terminal window and install pyLoad typing:

    pip install --pre pyload-ng[all]

To start pyLoad use the command:

    pyload

See the [usage section](#usage) for information on all available options.

If you want to uninstall pyLoad:

    pip uninstall pyload-ng

## Usage

    usage: pyload [-h] [-d] [-r] [--storagedir STORAGEDIR] [--userdir USERDIR]
                  [--tempdir TEMPDIR] [--dry-run] [--daemon] [--version]

    The free and open-source Download Manager written in pure Python

    optional arguments:
      -h, --help                    show this help message and exit
      -d, --debug                   enable debug mode
      -r, --reset                   reset default username/password
      --storagedir STORAGEDIR       use this location to save downloads
      --userdir USERDIR             use this location to store user data files
      --tempdir TEMPDIR             use this location to store temporary files
      --dry-run                     test start-up and exit
      --daemon                      run as daemon
      --version                     show program's version number and exit

To start pyLoad, type the command:

    pyload

This will create the following directories (if they don't exist already):

-   `~/Downloads/pyLoad`: where downloads will be saved.
-   `~/.pyload`: where user data and configuration files are stored.
-   `<TMPDIR>/pyLoad`: where temporary files are stored. `<TMPDIR>` is [platform-specific](https://docs.python.org/3/library/tempfile.html#tempfile.gettempdir).

> **Note**:
> On Windows, user data and configuration files are stored in the directory `~\AppData\Roaming\pyLoad`.

### Help

To show an overview of the available options, type:

    pyload --help

### Web Interface

Open your web browser and visit the url http://localhost:8000 to have access to
the pyLoad's web interface.

-   Default username: `pyload`.
-   Default password: `pyload`.

**It's highly recommended to change the default access credentials on first start**.

## Advanced Installation

### Stable Release

Get the latest stable release of pyLoad:

    pip install pyload-ng

> **Note**:
> No stable release yet, pyLoad is now in pre-release phase.

#### Available modules

-   `pyload.core`: pyLoad's heart.
-   `pyload.plugins`: the collection of officially supported plugins for pyLoad.
-   `pyload.webui`: a web interface to interact with pyLoad.

### Development Release

You can force the installation of the latest development release of pyLoad,
appending the option `--pre` to the installation command:

    pip install --pre pyload-ng

**Do not use development releases in production**. Unexpected crashes may occur.

### Extra Dependencies

Extra dependencies are non-essential packages that enable additional features of pyLoad.

To install them you have to append a specific tag name to the installation command.

#### Available tags

-   `plugins`: includes packages used by several plugins.
-   `build`: includes packages used to [build translations](#build-translations).
-   `all`: includes both plugins and build packages.

You can use a tag in this way:

    pip install pyload-ng[plugins]

Or group more together:

    pip install pyload-ng[plugins][build]

### Build Translations

Use the command `build_locale` to retrieve and build the latest locale files (translations):

    python setup.py build_locale

Invoke `build_locale` before building the package (eg. `bdist_wheel`).

> **Note**:
>
> You don't need to build the translations if you installed pyLoad through `pip`, they're already included.

## Report a Vulnerability

Please refer to [SECURITY](https://github.com/pyload/pyload/blob/main/SECURITY.md) to read our security policy.

## Contribute to pyLoad

Please refer to [CONTRIBUTING](https://github.com/pyload/pyload/blob/main/CONTRIBUTING.md) to read our contribution guidelines.

## Docker Images

[![Docker build status](https://img.shields.io/docker/build/pyload/pyload?style=flat-square)](https://hub.docker.com/r/pyload/pyload)
[![MicroBadger layers](https://img.shields.io/microbadger/layers/pyload/pyload?style=flat-square)](https://microbadger.com/images/pyload/pyload)
[![MicroBadger size](https://img.shields.io/microbadger/image-size/pyload/pyload?style=flat-square)](https://microbadger.com/images/pyload/pyload)

#### Available images

-   `pyload/pyload:alpine`: docker image for amd64, arm and arm64v8.
-   `pyload/pyload:ubuntu-arm32v7`: docker image for arm32v7.
-   `pyload/pyload`: alias of `pyload/pyload:alpine`.

### Create Container

    docker create --name=pyload -v <USERDIR>:/config -v <STORAGEDIR>:/downloads --restart unless-stopped pyload/pyload

> **Note**:
>
> Replace `<STORAGEDIR>` with the location on the host machine where you want that downloads will be saved.
>
> Replace `<USERDIR>` with where you want that user data files (configurations) are stored.

### Start Container

    docker start pyload

### Stop Container

    docker stop pyload

### Show Logs

    docker logs -f pyload

### Docker Compose

Compatible with `docker-compose` v2 schemas:

    ---
    version: '2'
    services:
      pyload:
        image: pyload
        build: <REPODIR>
        container_name: pyload
        environment:
          - PUID=1000
          - PGID=1000
          - TZ=Europe/London
        volumes:
          - <USERDIR>:/config
          - <STORAGEDIR>:/downloads
        ports:
          - 8000:8000 # Webinterface
          - 9666:9666 # Click 'N' Load
        restart: unless-stopped

> **Note**:
>
> Replace `<REPODIR>` with the location on the host machine where you have checked out the pyload repository.
>
> Replace `<STORAGEDIR>` with the location on the host machine where you want that downloads will be saved.
>
> Replace `<USERDIR>` with where you want that user data files (configurations) are stored.

## Troubleshooting

### pip not found

Retry replacing the command `pip` with `pip3`:

    pip3 install pyload-ng

If fails again, you may not have the Python interpreter
or the pip package manager installed on your system.

Try reinstalling Python to fix this issue.

Visit https://www.python.org/downloads
to get the proper **Python 3** release for your system.

### pyload-ng not found

Check the version of the Python interpreters installed on your system.

To show the version of your **default** Python interpreter, type the command:

    python --version

If the version is too old, try to upgrage Python, then you can retry to install pyLoad.

Python releases below version 3.6 are not supported!

### Setuptools is too old

To upgrade the `setuptools` package, type the command:

    pip install --upgrade setuptools

### Permission denied

Under Unix-based systems, try to install pyLoad with root privileges.

Prefix the installation/uninstallation command with `sudo`:

    sudo pip install pyload-ng
    sudo pip uninstall pyload-ng

Under Windows systems, open a _Command Prompt as administrator_ to install pyLoad
with root privileges.

You can also try to install the `pyload-ng` package **without** root privileges.

Append the option `--user` to the installation command:

    pip install --user pyload-ng

## Licensing

[![license](https://img.shields.io/pypi/l/pyload-ng?style=flat-square)](https://github.com/pyload/pyload/blob/main/LICENSE.md)
[![cla](https://cla-assistant.io/readme/badge/pyload/pyload)](https://cla-assistant.io/pyload/pyload)

### Open Source License

You are allowed to use this software under the terms of the **GNU Affero
General Public License** as published by the Free Software Foundation;
either **version 3** of the License, or (at your option) any later version.

Please refer to [LICENSE](https://github.com/pyload/pyload/blob/main/LICENSE.md) to read the project license.

### Alternative License

With an explicit permission of the **pyLoad team** you may use or distribute
this software under a different license according to the agreement.

### Contributor License Agreement

Please refer to [CLA](https://cla-assistant.io/pyload/pyload) for the full agreement conditions.

This is essentially what you will be agreeing to:

-   You claim to have the right to make the contribution
    (i.e. it's your own work).
-   You grant the project a perpetual, non-exclusive license to use the
    contribution.
-   You grant the project rights to change the outbound license that we use to
    distribute the code.
-   You retain full ownership (copyright) of your submission and are free to do
    with it as you please.

Contact us at licensing@pyload.net for any question about the pyLoad licensing policy.

## Credits

Please refer to [AUTHORS](https://github.com/pyload/pyload/blob/main/AUTHORS.md) to know a bit more about the people behind pyLoad.

<br />

---

###### © 2008-2024 pyLoad team
