# pyLoad

[![pyload.net](https://img.shields.io/badge/.net-pyload-orange.svg)](https://pyload.net)
[![wiki](https://img.shields.io/badge/docs-wiki-blue.svg)](https://github.com/pyload/pyload/wiki)
[![support](https://img.shields.io/badge/support-issues-red.svg)](https://github.com/pyload/pyload/issues)
[![Join the chat](https://badges.gitter.im/pyload/pyload.svg)](https://gitter.im/pyload/pyload?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
[![IRC Freenode](https://img.shields.io/badge/irc-freenode-lightgray.svg)](https://kiwiirc.com/client/irc.freenode.com/#pyload)
[![Twitter](https://img.shields.io/badge/-twitter-429cd6.svg?logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2CPD94bWwgdmVyc2lvbj0iMS4wIiA%2FPjwhRE9DVFlQRSBzdmcgIFBVQkxJQyAnLS8vVzNDLy9EVEQgU1ZHIDEuMC8vRU4nICAnaHR0cDovL3d3dy53My5vcmcvVFIvMjAwMS9SRUMtU1ZHLTIwMDEwOTA0L0RURC9zdmcxMC5kdGQnPjxzdmcgZW5hYmxlLWJhY2tncm91bmQ9Im5ldyAwIDAgMzIgMzIiIGhlaWdodD0iMzJweCIgaWQ9IkxheWVyXzEiIHZlcnNpb249IjEuMCIgdmlld0JveD0iMCAwIDMyIDMyIiB3aWR0aD0iMzJweCIgeG1sOnNwYWNlPSJwcmVzZXJ2ZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIiB4bWxuczp4bGluaz0iaHR0cDovL3d3dy53My5vcmcvMTk5OS94bGluayI%2BPHBhdGggZD0iTTMxLjk5Myw2LjA3N0MzMC44MTYsNi42LDI5LjU1Miw2Ljk1MywyOC4yMjMsNy4xMWMxLjM1NS0wLjgxMiwyLjM5Ni0yLjA5OCwyLjg4Ny0zLjYzICBjLTEuMjY5LDAuNzUxLTIuNjczLDEuMjk5LTQuMTY4LDEuNTkyQzI1Ljc0NCwzLjc5NywyNC4wMzgsMywyMi4xNDksM2MtMy42MjUsMC02LjU2MiwyLjkzOC02LjU2Miw2LjU2MyAgYzAsMC41MTQsMC4wNTcsMS4wMTYsMC4xNjksMS40OTZDMTAuMzAxLDEwLjc4NSw1LjQ2NSw4LjE3MiwyLjIyNyw0LjIwMWMtMC41NjQsMC45Ny0wLjg4OCwyLjA5Ny0wLjg4OCwzLjMgIGMwLDIuMjc4LDEuMTU5LDQuMjg2LDIuOTE5LDUuNDY0Yy0xLjA3NS0wLjAzNS0yLjA4Ny0wLjMyOS0yLjk3Mi0wLjgyMWMtMC4wMDEsMC4wMjctMC4wMDEsMC4wNTYtMC4wMDEsMC4wODIgIGMwLDMuMTgxLDIuMjYyLDUuODM0LDUuMjY1LDYuNDM3Yy0wLjU1LDAuMTQ5LTEuMTMsMC4yMy0xLjcyOSwwLjIzYy0wLjQyNCwwLTAuODM0LTAuMDQxLTEuMjM0LTAuMTE3ICBjMC44MzQsMi42MDYsMy4yNTksNC41MDQsNi4xMyw0LjU1OGMtMi4yNDUsMS43Ni01LjA3NSwyLjgxMS04LjE1LDIuODExYy0wLjUzLDAtMS4wNTMtMC4wMzEtMS41NjYtMC4wOTIgIEMyLjkwNSwyNy45MTMsNi4zNTUsMjksMTAuMDYyLDI5YzEyLjA3MiwwLDE4LjY3NS0xMC4wMDEsMTguNjc1LTE4LjY3NWMwLTAuMjg0LTAuMDA4LTAuNTY4LTAuMDItMC44NSAgQzMwLDguNTUsMzEuMTEyLDcuMzk1LDMxLjk5Myw2LjA3N3oiIGZpbGw9IiM1NUFDRUUiLz48Zy8%2BPGcvPjxnLz48Zy8%2BPGcvPjxnLz48L3N2Zz4%3D)](https://twitter.com/pyload)
[![Facebook](https://img.shields.io/badge/-facebook-3a589e.svg?logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2CPD94bWwgdmVyc2lvbj0iMS4wIiA%2FPjwhRE9DVFlQRSBzdmcgIFBVQkxJQyAnLS8vVzNDLy9EVEQgU1ZHIDEuMC8vRU4nICAnaHR0cDovL3d3dy53My5vcmcvVFIvMjAwMS9SRUMtU1ZHLTIwMDEwOTA0L0RURC9zdmcxMC5kdGQnPjxzdmcgZW5hYmxlLWJhY2tncm91bmQ9Im5ldyAwIDAgMzIgMzIiIGhlaWdodD0iMzJweCIgaWQ9IkxheWVyXzEiIHZlcnNpb249IjEuMCIgdmlld0JveD0iMCAwIDMyIDMyIiB3aWR0aD0iMzJweCIgeG1sOnNwYWNlPSJwcmVzZXJ2ZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIiB4bWxuczp4bGluaz0iaHR0cDovL3d3dy53My5vcmcvMTk5OS94bGluayI%2BPGc%2BPHBhdGggZD0iTTMyLDMwYzAsMS4xMDQtMC44OTYsMi0yLDJIMmMtMS4xMDQsMC0yLTAuODk2LTItMlYyYzAtMS4xMDQsMC44OTYtMiwyLTJoMjhjMS4xMDQsMCwyLDAuODk2LDIsMlYzMHoiIGZpbGw9IiMzQjU5OTgiLz48cGF0aCBkPSJNMjIsMzJWMjBoNGwxLTVoLTV2LTJjMC0yLDEuMDAyLTMsMy0zaDJWNWMtMSwwLTIuMjQsMC00LDBjLTMuNjc1LDAtNiwyLjg4MS02LDd2M2gtNHY1aDR2MTJIMjJ6IiBmaWxsPSIjRkZGRkZGIiBpZD0iZiIvPjwvZz48Zy8%2BPGcvPjxnLz48Zy8%2BPGcvPjxnLz48L3N2Zz4%3D)](https://www.facebook.com/pyload)

*pyLoad* is a free and open source downloader for 1-click-hosting sites.
It supports link decryption as well as all important container formats.
Targeted for headless NASs it is designed to be extremely lightweight, fully customizable and remotely manageable via web interface.

# Dependencies

You need at least Python 2.5 to run pyLoad and all of these required libraries, unless shipped with pyLoad.
They should be automatically installed when using pip install.
The prebuilt pyLoad packages also install these dependencies or have them included, so manual install
is only needed when installing pyLoad from source.

## Required

- pycurl a.k.a python-curl
- jinja2 (shipped with pyLoad)
- beaker (shipped with pyLoad)
- thrift (shipped with pyLoad)

Some plugins require additional packages, only install these when needed.

## Optional

- pycrypto: RSDF/CCF/DLC support
- tesseract, pillow (or python-pil a.k.a python-imaging): Automatic captcha recognition for a small amount of plugins
- jsengine (js2py, node, spidermonkey, ossp-js, pyv8, rhino): Used for several hoster, ClickNLoad
- feedparser
- BeautifulSoup (shipped with pyLoad)
- pyOpenSSL: For SSL connection

# First start

Note: If you installed pyLoad via package-manager `python pyLoadCore.py` is probably equivalent to `pyLoadCore`

Run:

    python pyLoadCore.py

and follow the instructions of the setup assistant.

For a list of options use:

    python pyLoadCore.py -h

# Configuration

After finishing the setup assistant pyLoad is ready to use and more configuration can be done via webinterface.
Additionally you could simply edit the config files located in your pyLoad home dir (defaults to: ~/.pyload)
with your favorite editor and edit the appropriate options. For a short description of
the options take a look at https://github.com/pyload/pyload/wiki/Configuration.

To restart the configure assistant run:

    python pyLoadCore.py -s

## Adding downloads

To start the CLI and connect to a local server, run:

    python pyLoadCli.py -l

for more options refer to:

    python pyLoadCli.py -h

The webinterface can be accessed when pointing your web browser to the ip and configured port, defaults to http://localhost:8000

# Notes

For more information, see https://pyload.net 
