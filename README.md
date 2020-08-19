<br />
<p align="center">
  <img src="https://raw.githubusercontent.com/pyload/pyload/master/media/banner.png" alt="pyLoad" height="110" />
</p>
<h2 align="center">The free and open-source Download Manager written in pure Python</h2>
<h4 align="center">
  <a href="#status">Status</a> |
  <a href="#installation">Installation</a> |
  <a href="#usage">Usage</a> |
  <a href="#docker-support-experimental">Docker Support</a> |
  <a href="#troubleshooting">Troubleshooting</a> |
  <a href="#licensing">Licensing</a> |
  <a href="#credits">Credits</a>
</h4>
<br />
<br />

## Status

[![Build Status](https://img.shields.io/travis/pyload/pyload.svg)](https://travis-ci.org/pyload/pyload)
[![Updates](https://pyup.io/repos/github/pyload/pyload/shield.svg)](https://pyup.io/repos/github/pyload/pyload)
[![Codacy Badge](https://img.shields.io/codacy/grade/240a2201eee54680b1c34bf86a32abd0.svg)](https://www.codacy.com/app/pyLoad/pyload)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![CLA assistant](https://cla-assistant.io/readme/badge/pyload/pyload)](https://cla-assistant.io/pyload/pyload)

- **pyLoad Next**, the newest version of pyLoad which resides in the [master branch](https://github.com/pyload/pyload/tree/master) and is deployed as `pyload-ng` on [PyPI](https://pypi.org/project/pyload-ng/).
  It only works on Python 3.6+ and it's in pre-alpha phase right now.

- **pyLoad Stable**, the old production ready grade version of pyLoad, which resides in the [stable branch](https://github.com/pyload/pyload/tree/stable) and is compatible with Python 2 only.

**This README covers everything regarding the first one only**.

## Installation

[![PyPI Status](https://img.shields.io/pypi/status/pyload-ng.svg)](https://pypi.python.org/pypi/pyload-ng)
[![PyPI Version](https://img.shields.io/pypi/v/pyload-ng.svg)](https://pypi.python.org/pypi/pyload-ng)
[![PyPI Python Versions](https://img.shields.io/pypi/pyversions/pyload-ng.svg)](https://pypi.python.org/pypi/pyload-ng)
[![PyPI License](https://img.shields.io/pypi/l/pyload-ng.svg)](https://github.com/pyload/pyload/blob/master/LICENSE.md)

To install pyLoad, type the command:

    pip install pyload-ng

This will install in your system the latest stable release of pyLoad.

> **Note**:
> No stable releases are available at the moment.

#### Available modules

- `pyload.core`: pyLoad's heart, you can't do anything without it!
- `pyload.plugins`: the complete collection of all supported plugins for pyLoad.
- `pyload.webui`: just a way to interact with pyLoad, web proof of course.

### Extra Dependencies

You can install all the recommended packages for pyLoad at once.

Append the tag `extra` to the installation command:

    pip install pyload-ng[extra]

#### Available tags

- `extra`: recommended extra packages.
- `build`: packages required to build locales.
- `all`: all of them.

You can also use more tags together:

    pip install pyload-ng[extra][build]

### Development Releases

You can force the installation of the latest development release of pyLoad,
appending the option `--pre` to the installation command:

    pip install --pre pyload-ng

**Do not use development releases in production**. Unexpected crashes may occur.

### Build Translations

> **Note**:
> You do not have to build any locale file if you installed pyLoad through `pip`,
> because they're all already included.

Use the command `build_locale` to retrieve and build the latest locale files (translations)
for your installation:

    python setup.py build_locale

It should be invoked **_before_** launching any other build/installation command (eg. `bdist_wheel`).

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
- `~/.pyload`: where configuration files are stored.
- `<TMPDIR>/pyLoad`: where temporary files are stored.

On Windows systems data files are saved in the directory `~\AppData\Roaming\pyLoad`.

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

## Docker Images [experimental]

[![Docker Build Status](https://img.shields.io/docker/build/pyload/pyload.svg)](https://hub.docker.com/r/pyload/pyload)
[![MicroBadger Layers](https://img.shields.io/microbadger/layers/pyload/pyload/latest-ubuntu.svg?label=layers%20%28ubuntu%29)](https://microbadger.com/images/pyload/pyload:latest-ubuntu)
[![MicroBadger Size](https://img.shields.io/microbadger/image-size/pyload/pyload/latest-ubuntu.svg?label=image%20size%20%28ubuntu%29)](https://microbadger.com/images/pyload/pyload:latest-ubuntu)

#### Available images

- `pyload/pyload:ubuntu`: default docker image for pyLoad.
- `pyload/pyload:alpine`: alternative docker image for pyLoad (smaller, [maybe slower](https://medium.com/@lih.verma/alpine-makes-python-docker-builds-way-too-50-slower-and-images-double-2-larger-61d1d43cbc79)).
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

### Installation

If the installation fails due any of the listed errors,
retry applying the given solution:

#### pip not found

Retry replacing the command `pip` with `pip3`:

    pip3 install pyload-ng

If still fails you may not have already installed on your system the Python interpreter
or the pip package manager.
Or maybe something else got corrupted somehow...

The easiest way to fix this error is to (re)install Python.

Visit https://www.python.org/downloads
to get the proper **Python 3** release for your system.

#### pyload-ng not found

Check the version of the Python interpreters installed on your system.

To show the version of your **default** Python interpreter, type the command:

    python --version

If the version is too old, try to upgrage Python, then you can retry to install pyLoad.

Python releases below version 3.6 are not supported!

#### Setuptools is too old

To upgrade the `setuptools` package, type the command:

    pip install --upgrade setuptools

#### Permission denied

Under Unix-based systems, try to install pyLoad with root privileges.

Prefix the installation command with `sudo`:

    sudo pip install pyload-ng

Under Windows systems, open a _Command Prompt as administrator_ to install pyLoad
with root privileges.

You can also try to install the `pyload-ng` package **without** root privileges.

Append the option `--user` to the installation command:

    pip install --user pyload-ng

### Uninstallation

To uninstall pyLoad, type the command:

    pip uninstall pyload-ng

> **Note:**
> This will not remove any installed dependencies.

#### Permission denied

Under Unix-based systems, try to uninstall pyLoad with root privileges.

Prefix the installation command with `sudo`:

    sudo pip uninstall pyload-ng

Under Windows systems, open a _Command Prompt as administrator_ to uninstall pyLoad
with root privileges.

## Licensing

### Open Source License

You are allowed to use this software under the terms of the **GNU Affero
General Public License** as published by the Free Software Foundation;
either **version 3** of the License, or (at your option) any later version.

Please refer to the included [LICENSE](/LICENSE) for the full license.

### Alternative License

With an explicit permission of the authors you may use or distribute
this software under a different license according to the agreement.

### Contributor License Agreement

Please refer to the included [CLA](https://cla-assistant.io/pyload/pyload) for the full agreement conditions.

This is essentially what you will be agreeing to:

- You claim to have the right to make the contribution
  (i.e. it's your own work).
- You grant the project a perpetual, non-exclusive license to use the
  contribution.
- You grant the project rights to change the outbound license that we use to
  distribute the code.
- You retain full ownership (copyright) of your submission and are free to do
  with it as you please.

Contact us at licensing@pyload.net for any question about our code licensing policy.

## Credits

Please refer to the included [AUTHORS](/AUTHORS.md) for the full credits.

<br />

---

###### © 2020 pyLoad team
