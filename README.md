<p align="center">
  <a href="https://pyload.net" target="_blank">
    <img src="https://raw.githubusercontent.com/pyload/pyload/develop/media/banner.png" alt="pyLoad" height="110" />
  </a>
</p>
<h2 align="center">The Free and open-source Download Manager written in pure Python</h2>
<p align="center">
  <img src="https://img.shields.io/pypi/status/pyload-dev.svg" alt="PyPI Status" />
  <a href="https://pypi.python.org/pypi/pyload-dev" target="_blank">
    <img src="https://img.shields.io/pypi/v/pyload-dev.svg" alt="PyPI Version" />
  </a>
  <img src="https://img.shields.io/pypi/pyversions/pyload-dev.svg" alt="PyPI Python Versions" />
  <a href="https://github.com/pyload/pyload/blob/develop/LICENSE.md" target="_blank">
    <img src="https://img.shields.io/pypi/l/pyload-dev.svg" alt="PyPI License" />
  </a>
</p>
<br />
<br />

pyLoad-ng development releases.

Includes `pyload-core`, `pyload-plugins`, `pyload-webui`, `pyload-cli`.

#### Warnings

- This package is intended for developer audience only, **do not use in production!**
- This package is automatically deployed from latest source code of pyLoad's `develop` branch.


Installation
------------

### Complete Installation [recommended]

To install pyLoad and all its optional dependencies,
type in a terminal/command prompt window (as root/administrator):

    pip install --pre pyload-dev[all]

### Minimum Installation

To install pyLoad (and its essential dependencies),
type in a terminal/command prompt window (as root/administrator):

    pip install --pre pyload-dev

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

### Web Interface

To start pyLoad in *WebUI mode*,
type in a terminal/command prompt window:

    pyload

To show the available options, type `pyload -h`:

    usage: pyload [-h] [--version] [-d] [--userdir USERDIR] [--cachedir CACHEDIR]
                  [--daemon] [--restore]

    Free and open-source Download Manager written in pure Python

    optional arguments:
      -h, --help           show this help message and exit
      --version            show program's version number and exit
      -d, --debug          enable debug mode
      --userdir USERDIR    run with custom user folder
      --cachedir CACHEDIR  run with custom cache folder
      --daemon             daemonmize after start
      --restore            restore default admin user

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
<br />

-------------------------
###### © 2018 pyLoad team
