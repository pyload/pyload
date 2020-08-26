<p align="center">
  <img src="https://raw.githubusercontent.com/pyload/pyload/main/media/logo.png" alt="pyLoad" height="100" />
</p>
<h2></h2>

### 0.5.0 (N/D)

- [All] Code rewritten to natively run under Python 3
- [All] Several Python 3.6+ optimizations
- [All] Dropped Python 2 support
- [Webui] Switched web server to CherryPy's Cheroot
- [Webui] Migrated to Flask framework (from Bottle.py)
- [Webui] Theme management
- [Webui] Fixed default theme
- [Webui] Interactive captcha support
- [All] Renewed project file-tree structure
- [All] Removed all the old crap in the codebase (dependecies, modules, etc.)
- [Core] Fully rewritten
- [Core] PyPI and easy install support
- [Plugins] Partially updated (to work within the new core)
- [Core] Previous API not changed (legacy)
- [All] Code style cleanup (pep8 compliant)
- [Webui] New built-in themes: PyPlex
- [Core] More debug logging features (verbose, traceback, framestack)
- [Webui] Develop mode
- [Webui] Auto-login feature
- [All] A lot of un-tracked fixes... :P
- ...

### 0.4.9 (2011-12-14)

- Fixed various encoding issues
- Many other fixes
- Rewritten `Unrar` plugin
- Some new plugins

### 0.4.8 (2011-10-04)

- Fixed download chunks on Windows
- GUI is working again, but may be unstable
- Improved download performance for high bandwith connections
- JSON-API, usable by external applications _(e.g. FlexGet for automatic RSS feed downloading)_
- Many new plugins _(by @zoidberg10)_

### 0.4.7 (2011-08-08)

- CLI file-checker
- Dropped GUI _(since no one maintaining it)_
- Internal optimizations and fixes
- New API
- New documentation
- Package summary in Web UI
- Swedisch translation

### 0.4.6 (2011-06-18)

- Huge amount of bugfixes
- Integration of the ultra-lightweight webserver [bjoern](https://github.com/jonashaag/bjoern)
- IPKG package for most routers and NAS
- Little improvements for CLI and Web UI
- Mirror detection within packages
- Multihoster plugins _(real-debrid.com, rehost.to, etc.)_
- pyload-cli package (without GUI) for Debian
- Some new plugins _(x7.to, wupload.com, etc.)_
- Support `Rhino` as JavaScript engine

### 0.4.5 (2011-03-15)

- `CaptchaTrader` plugin
- Captcha input via remote API _(Android client, etc.)_ and plugins _(IRC, XMMP, etc.)_
- Consistently login data for Web UI and other clients
- Layout improvements
- Many bugfixes
- Much faster connection for the clients, especially over slow connections
- New remote backend with optional XML-RPC
- New Web UI, no `django` needed anymore _(much faster and less ram consuming)_
- pyLoad Android client support

### 0.4.4 (2011-01-31)

- Bugfixes
- Download resume
- Fixed/Added plugins
- Multiple connections for each download (aka chunks support)
- New translations
- Overview page in GUI
- Proxy and downloadspeed limitation supports
- Remove finished links with one click in Web UI

### 0.4.3 (2010-11-27)

- Advanced and improved GUI
- Fixed hoster plugins issues
- Fixed memory leaks
- Improved account management
- Improved XDCC support
- Include JavaScript engine in Windows release _(full Click'n'Load support)_
- New built-in daemon mode
- New file-browser
- New hoster _(files.mail.ru, dl.free.fr, etc.)_

### 0.4.2 (2010-09-25)

- Configurable file permission and owner
- `Megaupload` premium support
- Packages sortable and editable in Web UI

### 0.4.1 (2010-09-06)

- German, Italian and Polish translations
- `Hotfile` and `Fileserve` premium support
- Integrate GUI with core
- Many little fixes and improvements
- Plugin updater
- Use JavaScript engine for some Click'n'Load links
- Windows and Ubuntu releases

### 0.4.0 (2010-08-17)

- Editable configs and accounts over API
- IRC and XMPP clients
- Many internal changes and improvements
- New config directory `~/.pyload`
- New `HotFolder` plugin
- New `Unrar` plugin
- Online check for some hosters

### 0.3.1 (2010-02-08)

- Better GUI updating
- Better system check
- Flashgot support
- Implemented JD's Click'n'Load v2
- New `watchfolder` for container (`links.txt` included)
- Prepared translation
- Resume downloads
- `Youtube` HD plugin

### 0.3.0 (2010-01-23)

- Added and updated plugins
- Adjustable download speed
- Bugfixes
- Client ↔ core connection over XML-RPC
- Hook system + external scripts support (sh, bat, etc.)
- New DLC-Key
- New package system
- Rewritten GUI
- Rewritten WUI

### 0.2.2 (2009-11-08)

- Many little changes

### 0.2.1 (2009-09-04)

- Bugfixes
- Web Interface

### 0.1.1 (2009-08-12)

- Bugfixes

### 0.1.0 (2009-08-02)

- Initial release

<br />

---

###### © 2020 pyLoad team
