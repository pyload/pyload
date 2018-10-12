# -*- coding: utf-8 -*-

import re
import sys
from subprocess import PIPE, Popen, call
from urllib.request import urlretrieve
from zipfile import ZipFile

from paver.easy import *
from paver.setuputils import setup

PROJECT_DIR = path(__file__).dirname()
sys.path.append(PROJECT_DIR)

options = environment.options
path("pyload").mkdir()

extradeps = []
if sys.version_info <= (2, 5):
    extradeps += "simplejson"

setup(
    name="pyload",
    version="0.5.0",
    description="Fast, lightweight and full featured download manager.",
    long_description=open(PROJECT_DIR / "README").read(),
    keywords=("pyload", "download-manager", "one-click-hoster", "download"),
    url="http://pyload.net",
    download_url="http://pyload.net/download",
    license="GPL v3",
    author="pyLoad Team",
    author_email="support@pyload.net",
    platforms=("Any",),
    # package_dir={'pyload': 'src'},
    packages=["pyload"],
    # package_data=find_package_data(),
    # data_files=[],
    include_package_data=True,
    # exluced from build but not from sdist
    exclude_package_data={"pyload": ["docs*", "tests*"]},
    # 'bottle >= 0.10.0' not in list, because its small and contain little modifications
    install_requires=["thrift >= 0.8.0", "jinja2", "pycurl", "Beaker"] + extradeps,
    extras_require={
        "SSL": ["pyOpenSSL"],
        "DLC": ["pycrypto"],
        "lightweight webserver": ["bjoern"],
        "RSS plugins": ["feedparser"],
    },
    # setup_requires=["setuptools_hg"],
    entry_points={
        "console_scripts": ["pyLoad = pyLoad:main", "pyLoadCli = pyLoadCli:main"]
    },
    zip_safe=False,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Topic :: Internet :: WWW/HTTP",
        "Environment :: Console",
        "Environment :: Web Environment",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2",
    ],
)

options(
    sphinx=Bunch(builddir="_build", sourcedir=""),
    get_source=Bunch(
        src="https://bitbucket.org/spoob/pyload/get/tip.zip", rev=None, clean=False
    ),
    thrift=Bunch(path="../thrift/trunk/compiler/cpp/thrift", gen=""),
    virtualenv=Bunch(dir="env", python="python2", virtual="virtualenv2"),
    cog=Bunch(pattern="*.py"),
)

# xgettext args
xargs = [
    "--from-code=utf-8",
    "--copyright-holder=pyLoad Team",
    "--package-name=pyLoad",
    "--package-version={}".format(options.version),
    "--msgid-bugs-address='bugs@pyload.net'",
]


@task
@needs("cog")
def html():
    """
    Build html documentation.
    """
    module = path("docs") / "pyload"
    module.rmtree()
    call_task("paver.doctools.html")


@task
@cmdopts(
    [
        ("src=", "s", "Url to source"),
        ("rev=", "r", "HG revision"),
        ("clean", "c", "Delete old source folder"),
    ]
)
def get_source(options):
    """
    Downloads pyload source from bitbucket tip or given rev.
    """
    if options.rev:
        options.url = "https://bitbucket.org/spoob/pyload/get/{}.zip".format(
            options.rev
        )

    pyload = path("pyload")

    if len(pyload.listdir()) and not options.clean:
        return
    elif pyload.exists():
        pyload.rmtree()

    urlretrieve(options.src, "pyload_src.zip")
    zip = ZipFile("pyload_src.zip")
    zip.extractall()
    path("pyload_src.zip").remove()

    folder = [x for x in path(".").dirs() if x.name.startswith("spoob-pyload-")][0]
    folder.move(pyload)

    change_mode(pyload, 0o644)
    change_mode(pyload, 0o755, folder=True)

    for file in pyload.files():
        if file.name.endswith(".py"):
            file.chmod(0o755)

    (pyload / ".hgtags").remove()
    (pyload / ".gitignore").remove()
    # (pyload / "docs").rmtree()

    f = open(pyload / "__init__.py", "wb")
    f.close()

    # options.setup.packages = find_packages()
    # options.setup.package_data = find_package_data()


@task
@needs("clean", "generate_setup", "minilib", "get_source", "setuptools.command.sdist")
def sdist():
    """
    Build source code package with distutils.
    """


@task
@cmdopts([("path=", "p", "Thrift path"), ("gen=", "g", "Extra --gen option")])
def thrift(options):
    """
    Generate Thrift stubs.
    """

    print("add import for TApplicationException manually as long it is not fixed")

    outdir = path("pyload") / "remote" / "thriftbackend"
    (outdir / "gen-py").rmtree()

    cmd = [
        options.thrift.path,
        "-strict",
        "-o",
        outdir,
        "--gen",
        "py:slots,dynamic",
        outdir / "pyload.thrift",
    ]

    if options.gen:
        cmd.insert(len(cmd) - 1, "--gen")
        cmd.insert(len(cmd) - 1, options.gen)

    print("running", cmd)

    p = Popen(cmd)
    p.communicate()

    (outdir / "thriftgen").rmtree()
    (outdir / "gen-py").move(outdir / "thriftgen")

    # create light ttypes
    from pyload.remote.socketbackend.create_ttypes import main

    main()


@task
def compile_js():
    """
    Compile .coffee files to javascript.
    """

    root = path("pyload") / "webui" / "media" / "js"
    for f in root.glob("*.coffee"):
        print("generate", f)
        coffee = Popen(["coffee", "-cbs"], stdin=open(f, "rb"), stdout=PIPE)
        yui = Popen(["yuicompressor", "--type", "js"], stdin=coffee.stdout, stdout=PIPE)
        coffee.stdout.close()
        content = yui.communicate()[0]
        with open(root / f.name.replace(".coffee", ".js"), "wb") as js:
            js.write("{% autoescape true %}\n")
            js.write(content)
            js.write("\n{% endautoescape %}")


@task
def generate_locale():
    """
    Generates localisation files.
    """

    EXCLUDE = [
        "BeautifulSoup.py",
        # "pyload/gui",
        "pyload/cli",
        "webui/locale",
        "webui/ajax",
        "webui/cnl",
        "webui/pyload",
        "setup.py",
    ]
    makepot("pyload", path("pyload"), EXCLUDE, "./pyLoad.py\n")

    # makepot("gui", path("pyload") / "gui", [], includes="./pyLoadGui.py\n")
    makepot("cli", path("pyload") / "cli", [], includes="./pyLoadCli.py\n")
    makepot("setup", "", [], includes="./pyload/setup.py\n")

    EXCLUDE = ["server_thread.py", "webui/media/default"]

    # strings from js files
    strings = set()

    for fi in path("pyload/webui").walkfiles():
        if not fi.name.endswith(".js") and not fi.endswith(".coffee"):
            continue
        with open(fi, "rb") as c:
            content = c.read()

            strings.update(re.findall(r"_\s*\(\s*\"([^\"]+)", content))
            strings.update(re.findall(r"_\s*\(\s*\'([^\']+)", content))

    trans = path("pyload") / "webui" / "translations.js"

    with open(trans, "wb") as js:
        for s in strings:
            js.write('_("{}")\n'.format(s))

    makepot(
        "django",
        path("pyload/webui"),
        EXCLUDE,
        "./{}\n".format(trans.relpath(), [".py", ".html"], ["--language=Python"]),
    )

    trans.remove()

    path("includes.txt").remove()

    print("Locale generated")


@task
def tests():
    call(["nosetests2"])


@task
def virtualenv(options):
    """
    Setup virtual environment.
    """
    if path(options.dir).exists():
        return

    call(
        [options.virtual, "--no-site-packages", "--python", options.python, options.dir]
    )
    print("$ source {}/bin/activate".format(options.dir))


@task
def clean_env():
    """
    Deletes the virtual environment.
    """
    env = path(options.virtualenv.dir)
    if env.exists():
        env.rmtree()


@task
@needs("generate_setup", "minilib", "get_source", "virtualenv")
def env_install():
    """
    Install pyLoad into the virtualenv.
    """
    venv = options.virtualenv
    call([path(venv.dir) / "bin" / "easy_install", "."])


@task
def clean():
    """
    Cleans build directories.
    """
    path("build").rmtree()
    path("dist").rmtree()


# helper functions


def walk_trans(path, EXCLUDE, endings=[".py"]):
    result = ""

    for f in path.walkfiles():
        if [True for x in EXCLUDE if x in f.dirname().relpath()]:
            continue
        if f.name in EXCLUDE:
            continue

        for e in endings:
            if f.name.endswith(e):
                result += "./{}\n".format(f.relpath())
                break

    return result


def makepot(domain, p, excludes=[], includes="", endings=[".py"], xxargs=[]):
    print("Generate {}.pot".format(domain))

    f = open("includes.txt", "wb")
    if includes:
        f.write(includes)

    if p:
        f.write(walk_trans(path(p), excludes, endings))

    f.close()

    call(
        ["xgettext", "--files-from=includes.txt", "--default-domain={}".format(domain)]
        + xargs
        + xxargs
    )

    # replace charset und move file
    with open("{}.po".format(domain, "rb")) as f:
        content = f.read()

    path("{}.po".format(domain).remove())
    content = content.replace("charset=CHARSET", "charset=UTF-8")

    with open("locale/{}.pot".format(domain, "wb")) as f:
        f.write(content)


def change_owner(dir, uid, gid):
    for p in dir.walk():
        p.chown(uid, gid)


def change_mode(dir, mode, folder=False):
    for p in dir.walk():
        if folder and p.isdir():
            p.chmod(mode)
        elif p.isfile() and not folder:
            p.chmod(mode)
