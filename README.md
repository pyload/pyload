<br />
<p align="center">
  <a href="https://pyload.net">
    <img src="https://raw.githubusercontent.com/pyload/pyload/master/media/banner.png" alt="pyLoad" height="110" />
  </a>
</p>
<h2 align="center">The Free and open-source Download Manager written in pure Python</h2>
<br />
<h3 align="center"><a href="#installation">Installation</a> | <a href="#usage">Usage</a> | <a href="#login-credentials">Login Credentials</a></h3>
<br />
<br />
<p align="center">
  <a href="https://travis-ci.org/pyload/pyload">
    <img src="https://travis-ci.org/pyload/pyload.svg" alt="Build Status" />
  </a>
  <a href="https://pyup.io/repos/github/pyload/pyload/">
    <img src="https://pyup.io/repos/github/pyload/pyload/shield.svg" alt="Updates" />
  </a>
  <a class="badge-align" href="https://www.codacy.com/app/pyLoad/pyload?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=pyload/pyload&amp;utm_campaign=Badge_Grade">
    <img src="https://api.codacy.com/project/badge/Grade/240a2201eee54680b1c34bf86a32abd0" alt="Codacy Badge" />
  </a>
  <a href="https://github.com/ambv/black">
    <img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Code style: black" />
  </a>
  <a href="https://cla-assistant.io/pyload/pyload">
    <img src="https://cla-assistant.io/readme/badge/pyload/pyload" alt="CLA assistant" />
  </a>
</p>
<p align="center">
  <img src="https://img.shields.io/pypi/status/pyload-ng.svg" alt="PyPI Status" />
  <a href="https://pypi.python.org/pypi/pyload-ng">
    <img src="https://img.shields.io/pypi/v/pyload-ng.svg" alt="PyPI Version" />
  </a>
  <img src="https://img.shields.io/pypi/pyversions/pyload-ng.svg" alt="PyPI Python Versions" />
  <a href="https://github.com/pyload/pyload/blob/develop/LICENSE.md">
    <img src="https://img.shields.io/pypi/l/pyload-ng.svg" alt="PyPI License" />
  </a>
</p>
<br />

pyLoad-ng development releases.

Includes `pyload-core`, `pyload-plugins`, `pyload-webui`, `pyload-cli`.

#### Warnings

- This package is automatically deployed from the [master codebase](https://github.com/pyload/pyload/tree/master) of the pyLoad repository.
- We recommend to use the [stable codebase](https://github.com/pyload/pyload/tree/stable) in production.


Installation
------------

### Complete Installation [recommended]

To install pyLoad and all its optional dependencies,
type in a terminal/command prompt window (as root/administrator):

    pip install --pre pyload-ng[all]

### Minimum Installation

To install pyLoad (and its essential dependencies),
type in a terminal/command prompt window (as root/administrator):

    pip install --pre pyload-ng

### Troubleshooting

If the installation fails due to an error related to the `pycurl` package,
you may have to install it apart, before installing pyLoad.

Currently, PycURL does not support Python releases later than version 3.6,
but un-official Windows binary packages for latest Python versions are available
on https://www.lfd.uci.edu/~gohlke/pythonlibs/#pycurl .

**As an example**,
to install *PycURL 7.43.1* for Python 3.7 on Windows 64-bit, you have to
download the file named `pycurl-7.43.1-cp37-cp37m-win_amd64.whl`
and type in a terminal/command prompt window (as root/administrator):

    pip install pycurl-7.43.1-cp37-cp37m-win_amd64.whl

When the installation succesfully finishes you can safely delete the downloaded file.

Visit http://pycurl.io/docs/latest/install.html to learn how to get and install
the appropriate PycURL package for your system.


Usage
-----

    usage: pyload [-h] [--version] [-d] [--userdir USERDIR] [--cachedir CACHEDIR]
                  [--daemon] [--restore]

    The Free and open-source Download Manager written in pure Python

    optional arguments:
      -h, --help           show this help message and exit
      --version            show program's version number and exit
      -d, --debug          enable debug mode
      --userdir USERDIR    run with custom user folder
      --cachedir CACHEDIR  run with custom cache folder
      --daemon             daemonmize after start
      --restore            restore default admin user

### Web Interface

To start pyLoad in *WebUI mode*,
type in a terminal/command prompt window:

    pyload

To show the available options, type:

    pyload -h

To access the web interface open your web browser and visit the url http://localhost:8001 .
You can change it afterward.

### Command Line Interface

To start pyLoad in *CLI mode*,
type terminal/command prompt window:

    pyload-cli

To show the available options, type:

    pyload-cli -h

### Login Credentials

Default username and password are `pyload`.

It's highly recommended to change them on the first start.


<br />

-------------------------
###### © 2019 pyLoad team
