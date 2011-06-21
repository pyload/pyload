import sys
import os.path


def RenameProcess(new_name):
    """ Renames the process calling the function to the given name. """
    if sys.platform != 'linux2':
        print 'Unsupported platform'
        return False
    try:
        import ctypes
        is_64 = os.path.exists('/lib64/libc.so.6')
        if is_64:
            libc = ctypes.CDLL('/lib64/libc.so.6')
        else:
            libc = ctypes.CDLL('/lib/libc.so.6')
        libc.prctl(15, new_name, 0, 0, 0)
        return True
    except:
        print "rename failed"
        return False
