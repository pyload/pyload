# -*- coding: utf-8 -*-
# Django settings for pyload project.

DEBUG = True
TEMPLATE_DEBUG = DEBUG

import os
import sys
import django

SERVER_VERSION = "0.4.2"

PROJECT_DIR = os.path.dirname(__file__)

#chdir(dirname(abspath(__file__)) + sep)

PYLOAD_DIR = os.path.join(PROJECT_DIR,"..","..")

sys.path.append(PYLOAD_DIR)


sys.path.append(os.path.join(PYLOAD_DIR, "module"))

import InitHomeDir
sys.path.append(pypath)

config = None
#os.chdir(PROJECT_DIR) # UNCOMMENT FOR LOCALE GENERATION

#DEBUG = config.get("general","debug")

try:
    import module.web.ServerThread
    if not module.web.ServerThread.core:
        raise Exception
    PYLOAD = module.web.ServerThread.core.server_methods
    config = module.web.ServerThread.core.config
except:
    import xmlrpclib
    ssl = ""

    from module.ConfigParser import ConfigParser
    config = ConfigParser()

    if config.get("ssl", "activated"):
        ssl = "s"

    server_url = "http%s://%s:%s@%s:%s/" % (
                                        ssl,
                                        config.username,
                                        config.password,
                                        config.get("remote", "listenaddr"),
                                        config.get("remote", "port")
                                        )

    PYLOAD = xmlrpclib.ServerProxy(server_url, allow_none=True)

try:
    import subprocess
    subprocess.Popen(["js", "-v"], bufsize=-1,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    JS = ["js"]
except:
    JS = []


TEMPLATE = config.get('webinterface','template')
DL_ROOT = os.path.join(PYLOAD_DIR, config.get('general','download_folder'))
LOG_ROOT = os.path.join(PYLOAD_DIR, config.get('log','log_folder'))

ADMINS = (
          # ('Your Name', 'your_email@domain.com'),
          )

MANAGERS = ADMINS

DATABASE_ENGINE = 'sqlite3'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
#DATABASE_NAME = os.path.join(PROJECT_DIR, 'pyload.db')             # Or path to database file if using sqlite3.
DATABASE_NAME = 'pyload.db'        # Or path to database file if using sqlite3.
DATABASE_USER = ''             # Not used with sqlite3.
DATABASE_PASSWORD = ''         # Not used with sqlite3.
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
if (django.VERSION[0] > 1 or django.VERSION[1] > 1) and os.name != "nt":
    zone = None
else:
    zone = 'Europe'
TIME_ZONE = zone

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = config.get("general","language")

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(PROJECT_DIR, "media/")


# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"

#MEDIA_URL = 'http://localhost:8000/media'
MEDIA_URL = '/media/' + config.get('webinterface','template') + '/'
#MEDIA_URL = os.path.join(PROJECT_DIR, "media/")

LOGIN_REDIRECT_URL = "/"

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/admin/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '+u%%1t&c7!e$0$*gu%w2$@to)h0!&x-r*9e+-=wa4*zxat%x^t'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
                    'django.template.loaders.filesystem.load_template_source',
                    'django.template.loaders.app_directories.load_template_source',
                    #     'django.template.loaders.eggs.load_template_source',
                    )


MIDDLEWARE_CLASSES = (
                    'django.middleware.gzip.GZipMiddleware',
                    'django.middleware.http.ConditionalGetMiddleware',
                    'django.contrib.sessions.middleware.SessionMiddleware',
                    'django.middleware.locale.LocaleMiddleware',
                    'django.middleware.common.CommonMiddleware',
                    'django.contrib.auth.middleware.AuthenticationMiddleware',
                    #'django.contrib.csrf.middleware.CsrfViewMiddleware',
                    'django.contrib.csrf.middleware.CsrfResponseMiddleware'
                      )

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
                 # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
                 # Always use forward slashes, even on Windows.
                 # Don't forget to use absolute paths, not relative paths.
                 os.path.join(PROJECT_DIR, "templates"),
                 )

INSTALLED_APPS = (
                  'django.contrib.auth',
                  'django.contrib.contenttypes',
                  'django.contrib.sessions',
                  #'django.contrib.sites',
                  'django.contrib.admin',
                  'pyload',
                  'ajax',
                  'cnl',
                  )


AUTH_PROFILE_MODULE = 'pyload.UserProfile'
LOGIN_URL = '/login/'
