# pyLoad

pyLoad is a free and open source downloader for 1-click-hosting sites like rapidshare.com or uploaded.to. It supports link decryption as well as all important container formats. pyLoad is written entirely in Python and is currently under heavy development.

For news, downloads, wiki, forum and further information visit <http://pyload.net/>

To report bugs, suggest features, ask a question, get the developer version
or help us out, visit [Github](http://github.com/pyload/pyload).

Documentation about extending pyLoad can be found at our [documentation](https://github.com/pyload/pyload/wiki) or join us at #pyload on irc.freenode.net

## Dependencies

You need at least python 2.5 to run pyLoad and all of these required libaries. They should be automatically installed when using pip install.
The prebuilt pyload packages also install these dependencies or have them included, so manuall install is only needed when installing pyLoad from source.

### Required

* pycurl a.k.a python-curl
* jinja2
* beaker
* thrift
* simplejson (for python 2.5)

Some plugins require additional packages, only install these when needed.

### Optional

* pycrypto: RSDF/CCF/DLC support
* tesseract, python-pil a.k.a python-imaging: Automatic captcha recognition for a small amount of plugins
* jsengine (spidermonkey, ossp-js, pyv8, rhino): Used for several hoster, ClickNLoad
* feedparser
* BeautifulSoup
* pyOpenSSL: For SSL connection

## First start

*Note: If you installed pyload via package-manager `python pyLoadCore.py` is probably equivalent to `pyLoadCore`!*

To start pyLoad you will need to just run

```bash
  python pyLoadCore.py
```

and follow the instructions of the setup assistent.

For a list of options use

```bash
  python pyLoadCore.py -h
```

## Configuration

After finishing the setup assistent pyLoad is ready to use and more configuration can be done via webinterface. Additionally you could simply edit the config files located in your pyLoad home dir (defaults to: ~/.pyload) with your favorite editor and edit the appropriate options. For a short description of the options take a look at http://pyload.net/configuration.

To restart the configure assistent run:

```bash
  python pyLoadCore.py -s
```

To start the CLI and connect to a local server, run

```bash
  python pyLoadCli.py -l
```

for more options refer to

```bash
  python pyLoadCli.py -h
```

The webinterface can be accessed when pointing your browser to the IP and configured port, defaults to http://localhost:8000

## Chef Cookbook for pyLoad

Thanks to the authors of the pyLoad Chef Cookbook, you can now install pyLoad using Chef. Refer to the [repository hosted on GitHub](https://github.com/gridtec/cookbook-pyload) for more information.

## Notes

For more information, see <http://pyload.net/>
