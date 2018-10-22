#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: vuolter

def daemon():
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as e:
        sys.stderr.write("fork #1 failed: {} ({})\n".format(e.errno, e.strerror))
        sys.exit(1)

    # decouple from parent environment
    os.setsid()
    os.umask(0)

    # do second fork
    try:
        pid = os.fork()
        if pid > 0:
            # exit from second parent, print(eventual PID before)
            print("Daemon PID {}".format(pid))
            sys.exit(0)
    except OSError as e:
        sys.stderr.write("fork #2 failed: {} ({})\n".format(e.errno, e.strerror))
        sys.exit(1)

    # Iterate through and close some file descriptors.
    for fd in range(0, 3):
        try:
            os.close(fd)
        except OSError:  #: ERROR as fd wasn't open to begin with (ignored)
            pass

    os.open(os.devnull, os.O_RDWR)  #: standard input (0)
    os.dup2(0, 1)  #: standard output (1)
    os.dup2(0, 2)

    pyload_core = Core()
    pyload_core.start()
    
    
def run(args=sys.argv[1:]):
    """
    Entry point for console_scripts
    """
    # change name to 'pyLoad'
    # from pyload.lib.rename_process import renameProcess
    # renameProcess('pyLoad')
    if "--daemon" in sys.argv:
        daemon()
    else:
        pyload_core = Core()
        try:
            pyload_core.start()
        except KeyboardInterrupt:
            pyload_core.log.info(_("killed pyLoad from Terminal"))
            pyload_core.shutdown()
            os._exit(1)
            
if __name__ == "__main__":
    run()
