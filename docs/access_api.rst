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

     $ thrift --gen (language) pyload.thrift

You find now a directory named :file:`gen-(language)`. For instruction how to use the generated files consider the docs
at the thrift wiki and the examples here http://wiki.apache.org/thrift/ThriftUsage.


=======
Example
=======
In case you want to use python, pyload has already all files included to access the api over rpc.

A basic script that prints out some information: ::

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


Using HTTP/JSON
---------------

Another maybe easier way, which does not require much setup is to access the JSON Api via HTTP.
For this reason the webinterface must be enabled.

=====
Login
=====

First you need to authenticate, if you using this within the webinterface and the user is logged the API is also accessible,
since they share the same cookie/session.

However, if you are building a external client and want to authenticate manually
you have to send your credentials ``username`` and ``password`` as
POST parameter to ``http://pyload-core/api/login``.

The result will be your session id. If you are using cookies, it will be set and you can use the API now.
In case you dont't have cookies enabled you can pass the session id as ``session`` POST parameter
so pyLoad can authenticate you.

===============
Calling Methods
===============

In general you can use any method listed at the :class:`Api <module.Api.Api>` documentation, which is also available to
the thriftbackend.

Access works simply via ``http://pyload-core/api/methodName``, where ``pyload-core`` is the ip address
or hostname including the webinterface port. By default on local access this would be `localhost:8000`.

The return value will be formatted in JSON, complex data types as dictionaries.
As mentionted above for a documentation about the return types look at the thrift specification file  :file:`module/remote/thriftbackend/pyload.thrift`.

==================
Passing parameters
==================

To pass arguments you have two choices.
Either use positional arguments, eg ``http://pyload-core/api/getFileData/1``, where 1 is the FileID, or use keyword arguments
supplied via GET or POST ``http://pyload-core/api/getFileData?fid=1``. You can find the argument names in the :class:`Api <module.Api.Api>`
documentation.

It is important that *all* arguments are in JSON format. So ``http://pyload-core/api/getFileData/1`` is valid because
1 represents an integer in json format. On the other hand if the method is expecting strings, this would be correct:
``http://pyload-core/api/getUserData/"username"/"password"``.

Strings are wrapped in double qoutes, because `"username"` represents a string in json format. It's not limited to strings and intergers,
every container type like lists and dicts are possible. You usually don't have to convert them. just use a json encoder before using them
in the HTTP request.

Please note that the data have to be urlencoded at last. (Most libaries will do that automatically)