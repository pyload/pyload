# Copyright 2013 Hardcoded Software (http://www.hardcoded.net)

# This software is licensed under the "BSD" License as described in the "LICENSE" file, 
# which should be included with this package. The terms are also available at 
# http://www.hardcoded.net/licenses/bsd_license

from gi.repository import GObject, Gio

def send2trash(path):
    try:
        f = Gio.File.new_for_path(path)
        f.trash(cancellable=None)
    except GObject.GError as e:
        raise OSError(e.message)
