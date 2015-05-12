#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import with_statement

from paver.easy import *
from paver.setuputils import setup
from paver.doctools import cog

import glob
import os
import sys
import shutil
import re
import urllib

from tempfile import mkdtemp
from subprocess import call, Popen, PIPE
from zipfile import ZipFile

PROJECT_DIR = path(__file__).dirname()
sys.path.append(PROJECT_DIR)

options = environment.options
path("pyload").mkdir()

extradeps = []
if sys.version_info <= (2, 5):
    extradeps += 'simplejson'

setup(
    name="pyload",
    version="0.4.10",
    description='Fast, lightweight and full featured download manager.',
    long_description=open(PROJECT_DIR / "README.md").read(),
    keywords = ("pyload", "download-manager", "one-click-hoster", "download"),
    url="http://pyload.org",
    download_url='http://pyload.org/download',
    license='GPL v3',
    author="pyLoad Team",
    author_email="support@pyload.org",
    platforms = ('Any',),
    # package_dir={'pyload': "src"},
    packages=["pyload"],
    # package_data=find_package_data(),
    # data_files=[],
    include_package_data=True,
    exclude_package_data={'pyload': ["docs*", "scripts*", "tests*"]},  #: exluced from build but not from sdist
    # 'bottle >= 0.10.0' not in list, because its small and contain little modifications
    install_requires=['thrift >= 0.8.0', 'jinja2', 'pycurl', 'Beaker', 'BeautifulSoup >= 3.2, < 3.3'] + extradeps,
    extras_require={
        'SSL': ["pyOpenSSL"],
        'DLC': ['pycrypto'],
        'lightweight webserver': ['bjoern'],
        'RSS plugins': ['feedparser'],
    },
    # setup_requires=["setuptools_hg"],
    entry_points={'console_scripts': ['pyLoadCore = pyLoadCore:main']},
    zip_safe=False,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Topic :: Internet :: WWW/HTTP",
        "Environment :: Console",
        "Environment :: Web Environment",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2"
    ]
)

options(
    sphinx=Bunch(
        builddir="_build",
        sourcedir=""
    ),
    get_source=Bunch(
        src="https://bitbucket.org/spoob/pyload/get/tip.zip",
        rev=None,
        clean=False
    ),
    thrift=Bunch(
        path="../thrift/trunk/compiler/cpp/thrift",
        gen=""
    ),
    virtualenv=Bunch(
        dir="env",
        python="python2",
        virtual="virtualenv2",
    ),
    cog=Bunch(
        pattern="*.py",
    )
)

# xgettext args
xargs = ["--language=Python", "--add-comments=L10N",
         "--from-code=utf-8", "--copyright-holder=pyLoad Team", "--package-name=pyLoad",
         "--package-version=%s" % options.version, "--msgid-bugs-address='bugs@pyload.org'"]


@task
@needs('cog')
def html():
    """Build html documentation"""
    module = path("docs") / "pyload"
    pyload.rmtree()
    call_task('paver.doctools.html')


@task
@cmdopts([
    ('src=', 's', 'Url to source'),
    ('rev=', 'r', "HG revision"),
    ("clean", 'c', 'Delete old source folder')
])


def get_source(options):
    """ Downloads pyload source from bitbucket tip or given rev"""
    if options.rev: options.url = "https://bitbucket.org/spoob/pyload/get/%s.zip" % options.rev

    pyload = path("pyload")

    if len(pyload.listdir()) and not options.clean:
        return
    elif pyload.exists():
        pyload.rmtree()

    urllib.urlretrieve(options.src, "pyload_src.zip")
    zip = ZipFile("pyload_src.zip")
    zip.extractall()
    path("pyload_src.zip").remove()

    folder = [x for x in path(".").dirs() if x.name.startswith("spoob-pyload-")][0]
    folder.shutil.move(pyload)

    change_mode(pyload, 0644)
    change_mode(pyload, 0755, folder=True)

    for file in pyload.files():
        if file.name.endswith(".py"):
            file.chmod(0755)

    (pyload / ".hgtags").remove()
    (pyload / ".gitignore").remove()
    #(pyload / "docs").rmtree()

    f = open(pyload / "__init__.py", "wb")
    f.close()

    # options.setup.packages = find_packages()
    # options.setup.package_data = find_package_data()


@task
@needs('clean', 'generate_setup', 'minilib', 'get_source', 'setuptools.command.sdist')
def sdist():
    """ Build source code package with distutils """


@task
@cmdopts([
    ('path=', 'p', 'Thrift path'),
    ('gen=', 'g', "Extra --gen option")
])


def thrift(options):
    """ Generate Thrift stubs """

    print "add import for TApplicationException manually as long it is not fixed"

    outdir = path("pyload") / "remote" / "thriftbackend"
    (outdir / "gen-py").rmtree()

    cmd = [options.thrift.path, "-strict", "-o", outdir, "--gen", "py:slots, dynamic", outdir / "pyload.thrift"]

    if options.gen:
        cmd.insert(len(cmd) - 1, "--gen")
        cmd.insert(len(cmd) - 1, options.gen)

    print "running", cmd

    p = Popen(cmd)
    p.communicate()

    (outdir / "thriftgen").rmtree()
    (outdir / "gen-py").shutil.move(outdir / "thriftgen")

    # create light ttypes
    from pyload.remote.socketbackend.create_ttypes import main
    main()


@task
def compile_js():
    """ Compile .coffee files to javascript"""

    root = path("pyload") / "web" / "media" / "js"
    for f in root.glob("*.coffee"):
        print "generate", f
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
    """ Generates localization files """

    EXCLUDE = ["BeautifulSoup.py", "web/locale", "web/ajax", "web/cnl", "web/pyload",
               "setup.py"]
    makepot("core", path("pyload"), EXCLUDE, "./pyload.py\n")

    makepot("setup", "", [], includes="./pyload/setup.py\n")

    EXCLUDE = ["ServerThread.py", "web/media/default"]

    # strings from js files
    strings = set()

    for fi in path("pyload/web").walkfiles():
        if not fi.name.endswith(".js") and not fi.endswith(".coffee"):
            continue
        with open(fi, "rb") as c:
            content = c.read()

            strings.update(re.findall(r"_\s*\(\s*\"([^\"]+)", content))
            strings.update(re.findall(r"_\s*\(\s*\'([^\']+)", content))

    trans = path("pyload") / "web" / "translations.js"

    with open(trans, "wb") as js:
        for s in strings:
            js.write('_("%s")\n' % s)

    makepot("django", path("pyload/web"), EXCLUDE, "./%s\n" % trans.relpath(), [".py", ".html"], ["--language=Python"])

    trans.remove()

    path("includes.txt").remove()

    print "Locale generated"


@task
@cmdopts([
    ('key=', 'k', 'api key')
])


def upload_translations(options):
    """ Uploads the locale files to translation server """
    tmp = path(mkdtemp())

    shutil.shutil.copy('locale/crowdin.yaml', tmp)
    os.mkdir(tmp / 'pyLoad')
    for f in glob.glob('locale/*.pot'):
        if os.path.isfile(f):
            shutil.shutil.copy(f, tmp / 'pyLoad')

    config = tmp / 'crowdin.yaml'
    with open(config, 'rb') as f:
        content = f.read()
    content = content.format(key=options.key, tmp=tmp)
    with open(config, 'wb') as f:
        f.write(content)

    call(['crowdin-cli', '-c', config, 'upload', 'source'])

    shutil.rmtree(tmp)

    print "Translations uploaded"


@task
@cmdopts([
    ('key=', 'k', 'api key')
])


def download_translations(options):
    """ Downloads the translated files from translation server """
    tmp = path(mkdtemp())

    shutil.shutil.copy('locale/crowdin.yaml', tmp)
    os.mkdir(tmp / 'pyLoad')
    for f in glob.glob('locale/*.pot'):
        if os.path.isfile(f):
            shutil.shutil.copy(f, tmp / 'pyLoad')

    config = tmp / 'crowdin.yaml'
    with open(config, 'rb') as f:
        content = f.read()
    content = content.format(key=options.key, tmp=tmp)
    with open(config, 'wb') as f:
        f.write(content)

    call(['crowdin-cli', '-c', config, 'download'])

    for language in (tmp / 'pyLoad').listdir():
        if not language.isdir():
            continue

        target = path('locale') / language.basename()
        print "Copy language %s" % target
        if target.exists():
            shutil.rmtree(target)

        shutil.copytree(language, target)

    shutil.rmtree(tmp)


@task
def compile_translations():
    """ Compile PO files to MO """
    for language in path('locale').listdir():
        if not language.isdir():
            continue

        for f in glob.glob(language / 'LC_MESSAGES' / '*.po'):
            print "Compiling %s" % f
            call(['msgfmt', '-o', f.replace('.po', '.mo'), f])


@task
def tests():
    call(["nosetests2"])


@task
def virtualenv(options):
    """Setup virtual environment"""
    if path(options.dir).exists():
        return

    call([options.virtual, "--no-site-packages", "--python", options.python, options.dir])
    print "$ source %s/bin/activate" % options.dir


@task
def clean_env():
    """Deletes the virtual environment"""
    env = path(options.virtualenv.dir)
    if env.exists():
        env.rmtree()


@task
@needs('generate_setup', 'minilib', 'get_source', 'virtualenv')
def env_install():
    """Install pyLoad into the virtualenv"""
    venv = options.virtualenv
    call([path(venv.dir) / "bin" / "easy_install", "."])


@task
def clean():
    """Cleans build directories"""
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
                result += "./%s\n" % f.relpath()
                break

    return result


def makepot(domain, p, excludes=[], includes="", endings=[".py"], xxargs=[]):
    print "Generate %s.pot" % domain

    with open("includes.txt", "wb") as f:
        if includes:
            f.write(includes)

        if p:
            f.write(walk_trans(path(p), excludes, endings))

    call(["xgettext", "--files-from=includes.txt", "--default-domain=%s" % domain] + xargs + xxargs)

    # replace charset und move file
    with open("%s.po" % domain, "rb") as f:
        content = f.read()

    path("%s.po" % domain).remove()
    content = content.replace("charset=CHARSET", "charset=UTF-8")

    with open("locale/%s.pot" % domain, "wb") as f:
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
