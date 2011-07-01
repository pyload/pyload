.. _access_api:

*********************
How to access the API
*********************

pyLoad has a very powerfull API with can be accessed in several ways.

Overview
--------

First of all, you need to know what you can do with our API. It lets you do all common task like
retrieving download status, manage queue, manage accounts, modify config and so on.

This document is not intended to explain every function in detail, for a complete listing
see :class:`Api <module.Api.Api>`.

Of course its possible to access the ``core.api`` attribute in plugins and hooks, but much more
interesting is the possibillity to call function from different programs written in many different languages.

pyLoad uses thrift as backend and provides its :class:`Api <module.Api.Api>` as service.
More information about thrift can be found here http://wiki.apache.org/thrift/.

Using Thrift
------------

Every thrift service has to define all data structures and declare every method which should be usable via rpc.
This file is located :file:`module/remote/thriftbackend/pyload.thrift`, its very helpful to inform about
arguments and detailed structure of return types. However it does not contain any information about what the functions does.

Assuming you want to use the API in any other language than python than check if it is
supported here http://wiki.apache.org/thrift/LibraryFeatures?action=show&redirect=LanguageSupport.

Now install thrift, for instructions see http://wiki.apache.org/thrift/ThriftInstallation.
If every thing went fine you are ready to generate the method stubs, the command basically looks like this. ::

     $thrift --gen (language) pyload.thrift

You find now a directory named :file:`gen-(language)`. For instruction how to use the generated files consider the docs
at the thrift wiki and the examples here http://wiki.apache.org/thrift/ThriftUsage


Example
-------
In case you want to use python, pyload has already all files included to access the api over rpc.
A basic script that prints out some information. ::

    from module.remote.thriftbackend.ThriftClient import ThriftClient, WrongLogin

    try:
        client = ThriftClient(host="127.0.0.1", port=7227, user="User", password="yourpw")
    except:
        print "Login was wrong"
        exit()

    print "Server version:", client.getServerVersion()
    print client.statusDownloads()
    q = client.getQueue()
    for p in q:
      data = client.getPackageData(p.pid)
      print "Package Name: ", data.name

That's all for now, pretty easy isn't it?
If you still have open questions come around in irc or post them at our pyload forum.