<br />
<p align="center">
  <img src="https://raw.githubusercontent.com/pyload/pyload/main/media/banner.png" alt="pyLoad" height="110" />
</p>
<h2 align="center">The free and open-source Download Manager written in pure Python</h2>
<h4 align="center">
  <a href="#status">Status</a> |
  <a href="#quick-start">Quick Start</a> |
  <a href="#advanced-installation">Advanced Installation</a> |
  <a href="#usage">Usage</a> |
  <a href="#docker-images">Docker Images</a> |
  <a href="#troubleshooting">Troubleshooting</a> |
  <a href="#licensing">Licensing</a> |
  <a href="#credits">Credits</a>
</h4>
<br />
<br />

## Status

[![Travis build status](https://img.shields.io/travis/com/pyload/pyload/main)](https://travis-ci.com/pyload/pyload)
[![PyUp updates](https://pyup.io/repos/github/pyload/pyload/shield.svg)](https://pyup.io/repos/github/pyload/pyload)
[![Codacy grade](https://img.shields.io/codacy/grade/1d047f77c0a6496eb708e1b3ca83006b)](https://www.codacy.com/gh/pyload/pyload)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000)](https://github.com/ambv/black)
[![CLA assistant](https://cla-assistant.io/readme/badge/pyload/pyload)](https://cla-assistant.io/pyload/pyload)

**pyLoad Next** is the newest version of pyLoad.

Developed in the [main branch](https://github.com/pyload/pyload/tree/main) on GitHub and deployed as `pyload-ng` on [PyPI](https://pypi.org/project/pyload-ng/), works on Python 3.6+ and is currently in alpha phase.

The old stable version of pyLoad resides in the [stable branch](https://github.com/pyload/pyload/tree/stable) and is only compatible with Python 2.

## Quick Start

[![PyPI status](https://img.shields.io/pypi/status/pyload-ng)](https://pypi.python.org/pypi/pyload-ng)
[![PyPI version](https://img.shields.io/pypi/v/pyload-ng?label=version)](https://pypi.python.org/pypi/pyload-ng)
[![PyPI format](https://img.shields.io/pypi/format/pyload-ng)](https://pypi.python.org/pypi/pyload-ng)
[![PyPI python version](https://img.shields.io/pypi/pyversions/pyload-ng)](https://pypi.python.org/pypi/pyload-ng)
[![PyPI implementation](https://img.shields.io/pypi/implementation/pyload-ng)](https://pypi.python.org/pypi/pyload-ng)
[![PyPI license](https://img.shields.io/pypi/l/pyload-ng)](https://github.com/pyload/pyload/blob/main/LICENSE.md)

Open a terminal window and install pyLoad typing:

    pip install --pre pyload-ng[all]

To start pyLoad use the command:

    pyload

See the [usage section](#usage) for information on all available options.

If you want to uninstall pyLoad:

    pip uninstall pyload-ng

## Advanced Installation

Get the latest stable release of pyLoad:

    pip install pyload-ng

> **Note**:
> No stable releases are available at the moment.

#### Available modules

- `pyload.core`: pyLoad's heart.
- `pyload.plugins`: the collection of officially supported plugins for pyLoad.
- `pyload.webui`: a web interface to interact with pyLoad.

### Extra Dependencies

Extra dependencies are non-essential packages that extend or unlock some features of pyLoad.

To install them you have to append a specific tag name to the installation command.

#### Available tags

- `plugins`: packages required by some plugins to work.
- `build`: packages required to [build translations](#build-translations).
- `all`: alias of `build` and `plugins`.

You can use a tag in this way:

    pip install pyload-ng[plugins]

Or group more together:

    pip install pyload-ng[plugins][build]

### Development Releases

You can force the installation of the latest development release of pyLoad,
appending the option `--pre` to the installation command:

    pip install --pre pyload-ng

**Do not use development releases in production**. Unexpected crashes may occur.

### Build Translations

> **Note**:
> You don't have to build the translations files if you installed pyLoad through `pip`,
> because they're already included.

Use the command `build_locale` to retrieve and build the latest locale files (translations):

    python setup.py build_locale

**Invoke it before launching any other build/installation command** (eg. `bdist_wheel`).

## Usage

    usage: pyload [-h] [--version] [-d] [--userdir USERDIR] [--tempdir TEMPDIR]
                  [--daemon] [--restore]

    The free and open-source Download Manager written in pure Python

    optional arguments:
      -h, --help               show this help message and exit
      --version                show program's version number and exit
      -d, --debug              enable debug mode
      --userdir USERDIR        use this location to store user data files
      --tempdir TEMPDIR        use this location to store temporary files
      --storagedir STORAGEDIR  use this location to save downloads
      --daemon                 run as daemon
      --restore                reset default username/password

To start pyLoad, type the command:

    pyload

This will create the following directories (if they do not already exist):

- `~/Downloads/pyLoad`: where downloads will be saved.
- `~/.pyload`: where configuration files are stored\*.
- `<TMPDIR>/pyLoad`: where temporary files are stored.

On Windows systems configuration files are saved in the directory `~\AppData\Roaming\pyLoad`.

The location of `<TMPDIR>` is [platform-specific](https://docs.python.org/3/library/tempfile.html#tempfile.gettempdir).

### Command Options

To show an overview of the available options, type:

    pyload --help

### Web Interface

Open your web browser and visit the url http://localhost:8000 to have access to
the pyLoad's web interface.

- Default username: `pyload`.
- Default password: `pyload`.

**It's highly recommended to change the default access credentials on first start**.

## Docker Images

[![Docker build status](https://img.shields.io/docker/build/pyload/pyload)](https://hub.docker.com/r/pyload/pyload)
[![MicroBadger layers](https://img.shields.io/microbadger/layers/pyload/pyload)](https://microbadger.com/images/pyload/pyload)
[![MicroBadger size](https://img.shields.io/microbadger/image-size/pyload/pyload)](https://microbadger.com/images/pyload/pyload)

#### Available images

- `pyload/pyload:ubuntu`: default docker image of pyLoad (amd64, arm, arm64v8).
- `pyload/pyload:ubuntu-arm32v7`: default docker image of pyLoad (arm32v7).
- `pyload/pyload:alpine`: alternative docker image of pyLoad (maybe smaller).
- `pyload/pyload`: alias of `pyload/pyload:ubuntu`.

### Create Container

    docker create --name=pyload -v <USERDIR>:/config -v <STORAGEDIR>:/downloads --restart unless-stopped pyload/pyload

Replace `<STORAGEDIR>` with the location on the host machine where you want that downloads will be saved.

Replace `<USERDIR>` with where you want that user data files (configurations) are stored.

### Start Container

    docker start pyload

### Stop Container

    docker stop pyload

### Show Logs

    docker logs -f pyload

### Docker Compose

Compatible with `docker-compose` v2 schemas:

    ---
    version: 2
    services:
      pyload:
        image: pyload/pyload
        container_name: pyload
        environment:
          - PUID=1000
          - PGID=1000
          - TZ=Europe/London
        volumes:
          - <USERDIR>:/config
          - <STORAGEDIR>:/downloads
        ports:
          - 8000:8000
        restart: unless-stopped

Replace `<STORAGEDIR>` with the location on the host machine where you want that downloads will be saved.

Replace `<USERDIR>` with where you want that user data files (configurations) are stored.

## Troubleshooting

### pip not found

Retry replacing the command `pip` with `pip3`:

    pip3 install pyload-ng

If still fails you may not have already installed on your system the Python interpreter
or the pip package manager.
Or maybe something else got corrupted somehow...

The easiest way to fix this error is to (re)install Python.

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

### Open Source License

You are allowed to use this software under the terms of the **GNU Affero
General Public License** as published by the Free Software Foundation;
either **version 3** of the License, or (at your option) any later version.

Please refer to the [LICENSE](/LICENSE) for the full license.

### Alternative License

With an explicit permission of the **pyLoad team** you may use or distribute
this software under a different license according to the agreement.

### Contributor License Agreement

Please refer to the [CLA](https://cla-assistant.io/pyload/pyload) for the full agreement conditions.

This is essentially what you will be agreeing to:

- You claim to have the right to make the contribution
  (i.e. it's your own work).
- You grant the project a perpetual, non-exclusive license to use the
  contribution.
- You grant the project rights to change the outbound license that we use to
  distribute the code.
- You retain full ownership (copyright) of your submission and are free to do
  with it as you please.

Contact us at licensing@pyload.net for any question about pyLoad licensing policy.

## Credits

Please refer to the [AUTHORS](/AUTHORS.md) for the full credits.

<br />

---

###### © 2020 pyLoad team
