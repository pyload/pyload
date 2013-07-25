# -*- coding: utf-8 -*-

from paver.easy import *
from paver.doctools import cog

import fnmatch

# patch to let it support list of patterns
def new_fnmatch(self, pattern):
    if type(pattern) == list:
        for p in pattern:
            if fnmatch.fnmatch(self.name, p):
                return True
        return False
    else:
        return fnmatch.fnmatch(self.name, pattern)


path.fnmatch = new_fnmatch

import os
import sys
import shutil
from glob import glob
from tempfile import mkdtemp
from subprocess import call, Popen

PROJECT_DIR = path(__file__).dirname()
sys.path.append(PROJECT_DIR)

from pyload import __version__

options = environment.options
options(
    sphinx=Bunch(
        builddir="_build",
        sourcedir=""
    ),
    apitypes=Bunch(
        path="thrift",
    ),
    virtualenv=Bunch(
        dir="env",
        python="python2",
        virtual="virtualenv2",
    ),
    cog=Bunch(
        pattern=["*.py", "*.rst"],
    )
)

# xgettext args
xargs = ["--language=Python", "--add-comments=L10N",
         "--from-code=utf-8", "--copyright-holder=pyLoad Team", "--package-name=pyload",
         "--package-version=%s" % __version__, "--msgid-bugs-address='bugs@pyload.org'"]

# Modules replace rules
module_replace = [
('from module.plugins.Hoster import Hoster', 'from pyload.plugins.Hoster import Hoster'),
('from module.plugins.Hook import threaded, Expose, Hook', 'from pyload.plugins.Addon import threaded, Expose, Addon'),
('from module.plugins.Hook import Hook', 'from pyload.plugins.Addon import Addon'),
('from module.common.json_layer import json_loads, json_dumps', 'from pyload.utils import json_loads, json_dumps'),
('from module.common.json_layer import json_loads', 'from pyload.utils import json_loads'),
('from module.common.json_layer import json_dumps', 'from pyload.utils import json_dumps'),
('from module.utils import parseFileSize', 'from pyload.utils import parseFileSize'),
('from module.utils import save_join, fs_encode', 'from pyload.utils.fs import save_join, fs_encode'),
('from module.utils import save_join', 'from pyload.utils.fs import save_join'),
('from module.utils import fs_encode', 'from pyload.utils.fs import fs_encode'),
('from module.', 'from pyload.')  # This should be always the last one
]


@task
@needs('cog')
def html():
    """Build html documentation"""
    module = path("docs") / "pyload"
    module.rmtree()
    call_task('paver.doctools.html')



@task
@cmdopts([
    ('path=', 'p', 'Thrift path'),
])
def apitypes(options):
    """ Generate data types stubs """

    outdir = PROJECT_DIR / "pyload" / "remote"

    if (outdir / "gen-py").exists():
        (outdir / "gen-py").rmtree()

    cmd = [options.apitypes.path, "-strict", "-o", outdir, "--gen", "py:slots,dynamic", outdir / "pyload.thrift"]

    print "running", cmd

    p = Popen(cmd)
    p.communicate()

    (outdir / "thriftgen").rmtree()
    (outdir / "gen-py").move(outdir / "thriftgen")

    #create light ttypes
    from pyload.remote.create_apitypes import main

    main()
    from pyload.remote.create_jstypes import main

    main()


@task
def webapp():
    """ Builds the pyload web app. Nodejs and npm must be installed """

    os.chdir(PROJECT_DIR / "pyload" / "web")

    # Preserve exit codes
    ret = call(["npm", "install", "--no-color"])
    if ret:
        exit(ret)
    ret = call(["bower", "install", "--no-color"])
    if ret:
        exit(ret)
    ret = call(["grunt", "--no-color"])
    if ret:
        exit(ret)


@task
def generate_locale():
    """ Generates localisation files """
    # TODO restructure, many references are outdated

    EXCLUDE = ["pyload/lib", "pyload/cli", "pyload/setup", "pyload/plugins", "Setup.py"]

    makepot("core", path("pyload"), EXCLUDE)
    makepot("plugins", path("pyload") / "plugins")
    makepot("setup", "", [], includes="./pyload/Setup.py\n")
    makepot("cli", path("pyload") / "cli", [])

    # TODO: web ui

    path("includes.txt").remove()

    print "Locale generated"

@task
@cmdopts([
    ('key=', 'k', 'api key')
])
def upload_translations(options):
    """ Uploads the locale files to translation server """
    tmp = path(mkdtemp())

    shutil.copy('locale/crowdin.yaml', tmp)
    os.mkdir(tmp / 'pyLoad')
    for f in glob('locale/*.pot'):
        if os.path.isfile(f):
            shutil.copy(f, tmp / 'pyLoad')

    config = tmp / 'crowdin.yaml'
    content = open(config, 'rb').read()
    content = content.format(key=options.key, tmp=tmp)
    f = open(config, 'wb')
    f.write(content)
    f.close()

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

    shutil.copy('locale/crowdin.yaml', tmp)
    os.mkdir(tmp / 'pyLoad')
    for f in glob('locale/*.pot'):
        if os.path.isfile(f):
            shutil.copy(f, tmp / 'pyLoad')

    config = tmp / 'crowdin.yaml'
    content = open(config, 'rb').read()
    content = content.format(key=options.key, tmp=tmp)
    f = open(config, 'wb')
    f.write(content)
    f.close()

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

        for f in glob(language / 'LC_MESSAGES' / '*.po'):
            print "Compiling %s" % f
            call(['msgfmt', '-o', f.replace('.po', '.mo'), f])

@task
def tests():
    """ Run complete test suite """
    call(["tests/run_pyload.sh"])
    call(["tests/nosetests.sh"])
    call(["tests/quit_pyload.sh"])


@task
@cmdopts([
    ('virtual=', 'v', 'virtualenv path'),
    ('python=', 'p', 'python path')
])
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
def clean():
    """Cleans build directories"""
    path("build").rmtree()
    path("dist").rmtree()


@task
def replace_module_imports():
    """Replace imports from stable syntax to master"""
    for root, dirnames, filenames in os.walk('pyload/plugins'):
        for filename in fnmatch.filter(filenames, '*.py'):
            path = os.path.join(root, filename)
            f = open(path, 'r')
            content = f.read()
            f.close()
            for rule in module_replace:
                content = content.replace(rule[0], rule[1])
            if '/addons/' in path:
                content = content.replace('(Hook):', '(Addon):')
            f = open(path, 'w')
            f.write(content)
            f.close()


#helper functions

def walk_trans(path, EXCLUDE, endings=[".py"]):
    result = ""

    for f in path.walkfiles():
        if [True for x in EXCLUDE if x in f.dirname().relpath()]: continue
        if f.name in EXCLUDE: continue

        for e in endings:
            if f.name.endswith(e):
                result += "./%s\n" % f.relpath()
                break

    return result


def makepot(domain, p, excludes=[], includes="", endings=[".py"], xxargs=[]):
    print "Generate %s.pot" % domain

    f = open("includes.txt", "wb")
    if includes:
        f.write(includes)

    if p:
        f.write(walk_trans(path(p), excludes, endings))

    f.close()

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
