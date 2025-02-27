# based on https://github.com/NixOS/nixpkgs/commit/c0914a76c40230fb06eb6df8f54995796edef3ef
# Date:   Sun Mar 21 03:18:15 2021 +0100

# see also
# https://github.com/NixOS/nixpkgs/pull/242260 # pyload-ng: init at 0.5.0b3.dev72
# https://github.com/NixOS/nixpkgs/blob/master/pkgs/applications/networking/pyload-ng/default.nix

# usage:
# webinterface http://localhost:8000/
# user: pyload
# password: pyload

# to solve captchas, you also need these browser extensions
# https://github.com/RemiRigal/Yape
# https://github.com/Tampermonkey/tampermonkey
# https://github.com/guilryder/chrome-extensions/tree/main/xframe_ignore

{ lib
, fetchFromGitHub
, fetchpatch
, python3
#, python311
, gocr
, unrar
, rhino
, spidermonkey
, buildPythonApplication
}:

#let python3 = python311; in

buildPythonApplication rec {
  pname = "pyload";

  # versions https://github.com/pyload/pyload/issues/4339
  # https://pypi.org/project/pyload-ng/#history
  version = "0.5.0b3.dev82-unstable"; # 2024-04-21

  src =
  if true then ../. else
  fetchFromGitHub {
    owner = "pyload";
    repo = "pyload";
    rev = "08a759aaf2f7f776801821f582e310bae6a09308";
    hash = "sha256-B7W0r2QqhaY5lmocvZ8UVwG2y2Qz8CaHGIocQgVGt8U=";
  };

  # relax versions
  postPatch = ''
    sed -i -E 's/([a-zA-Z0-9_-]+)~=/\1>=/' setup.cfg
  '';

  # TODO add more deps, so we can use more features
  # https://github.com/pyload/pyload/blob/main/setup.cfg
  buildInputs = [
  ] ++ (with python3.pkgs; [
    paver
  ]);

  propagatedBuildInputs = [
    # TODO are these actually available on runtime?
    unrar # unfree
    rhino
    spidermonkey
    gocr
  ] ++ (with python3.pkgs; [
    pycurl
    jinja2
    # fix: error: Package ‘python3.10-Beaker-1.11.0’ in /nix/store/qb3dg4cx5jzk3pa8szzi0ziwnqy33p50-source/pkgs/development/python-modules/beaker/default.nix:72 is marked as insecure, refusing to evaluate.
    # also, beaker is not needed any more
    # also, beaker depends on pycryptopp, which is broken for python3.10 (last binary release for python3.9)
    #beaker
    thrift
    simplejson
    pycrypto
    feedparser
    tkinter
    beautifulsoup4
    send2trash
    # FIXME error: js2py-0.74 not supported for interpreter python3.12
    # js2py is required: ModuleNotFoundError: No module named 'dukpy'
    js2py
    # FIXME: ERROR: Could not find a version that satisfies the requirement Flask>=2.3.0; python_version >= "3.8"
    # pkgs.python3.pkgs.flask.version = "2.2.5"
    # https://github.com/NixOS/nixpkgs/pull/245320 # python3.pkgs.flask: 2.2.5 -> 2.3.2
    flask
    flask-compress
    flask-caching
    flask-themes2
    filetype
    semver
    cheroot
    cryptography
    flask-babel
    flask-session
    flask-session2
    bitmath
    setuptools # pkg_resources https://github.com/pyload/pyload/issues/4143
    certifi

    # aia # TODO use pypi relase instead of src/pyload/core/network/http/aia.py
    # extra deps for aia:
    pyopenssl
    timeout-decorator

    # hot-reload
    #jurigged
    #reloading
    #watchdog

    # optional dependencies
    colorlog # colorful console logging
    pillow # for some CAPTCHA plugin
    slixmpp # XMPP plugin
  ]);

  doCheck = false; # FIXME?

  meta = with lib; {
    description = "Free and open source downloader for 1-click-hosting sites";
    homepage = "https://github.com/pyload/pyload";
    license = licenses.gpl3;
    #maintainers = with maintainers; [];
    platforms = platforms.all;
  };
}
