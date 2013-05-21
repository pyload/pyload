try:
    import paver.tasks
except ImportError:
    from os.path import exists
    if exists("paver-minilib.zip"):
        import sys
        sys.path.insert(0, "paver-minilib.zip")
    import paver.tasks

paver.tasks.main()
