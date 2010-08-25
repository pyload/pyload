"""
Management utility to create superusers.
"""

import os
import sys

os.environ["DJANGO_SETTINGS_MODULE"] = 'settings'
sys.path.append(os.path.join(pypath, "module", "web"))

import getpass
import re
from optparse import make_option
from django.contrib.auth.models import User
from django.core import exceptions
from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext as _

RE_VALID_USERNAME = re.compile('[\w.@+-]+$')


def handle(username, email):
    #username = options.get('username', None)
    #email = options.get('email', None)
    interactive = False
    
    # Do quick and dirty validation if --noinput
    if not interactive:
        if not username or not email:
            raise CommandError("You must use --username and --email with --noinput.")
        if not RE_VALID_USERNAME.match(username):
            raise CommandError("Invalid username. Use only letters, digits, and underscores")

    password = ''
    default_username = ''
    
    User.objects.create_superuser(username, email, password)
    print "Superuser created successfully."

if __name__ == "__main__":
    username = sys.argv[1]
    email = sys.argv[2]
    handle(username, email)