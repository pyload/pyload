{ pkgs ? import <nixpkgs> { }
  #pkgs ? import ./. {}
}:

pkgs.mkShell {
  buildInputs =
  with pkgs;
  [

    # propagatedBuildInputs
    # TODO are these actually available on runtime?
    unrar # unfree
    rhino
    spidermonkey
    gocr

    (python3.withPackages (pp: with pp; [
      requests
      # buildInputs
      paver

    # propagatedBuildInputs
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

    # version switch since pyload 1da386c2
    #js2py # python <3.12
    dukpy # python >=3.12

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

    #flask-session2
    #(python3.pkgs.callPackage ./nix/flask-session2.nix { })
    (pp.callPackage ./nix/flask-session2.nix { })

    bitmath
    setuptools # pkg_resources https://github.com/pyload/pyload/issues/4143
    certifi

    # aia # TODO use pypi relase instead of src/pyload/core/network/http/aia.py
    # extra deps for aia:
    pyopenssl
    timeout-decorator

    # hot-reload
    #jurigged
    (pp.callPackage ./nix/jurigged.nix {
      codefind = pp.callPackage ./nix/codefind.nix { };
      giving = pp.callPackage ./nix/giving.nix { };
      ovld = pp.callPackage ./nix/ovld.nix { };
    })
    #reloading
    watchdog

    # optional dependencies
    colorlog # colorful console logging
    pillow # for some CAPTCHA plugin
    slixmpp # XMPP plugin

    ]))
  ];
}
