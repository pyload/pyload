.. _json_api:

========
JSON API
========

JSON [1]_ is a lightweight object notation and wrappers exist for nearly every programming language. Every
modern browser is able to load JSON objects with JavaScript. Unlike to thrift you don't need to generate or precompile
any stub methods, the JSON :class:`Api <module.Api.Api>` is ready to be used in most languages. The library is really lightweight (at least in python)
and you can build very lightweight scripts with it. Because of the builtin support, JSON is the first choice for all browser
applications.

In our case JSON is just the output format, you have exactly the same methods available as with the thrift backend. The only
difference is the underlying protocol.

Are there still reasons to choose the original :doc:`thrift <thrift_api>` backend in favor to JSON? Yes, since it
uses a binary protocol the performance will be better (when generating the objects), traffic will be smaller and
therefore the transfer faster.
In most IDEs you will get code completion, because of the pre-generated classes, which can make work much easier.

If you intend to write a full client you should prefer thrift if the language is supported, for lightweight scripts and
in browser environments JSON will be the better choice.

Login
-----

First you need to authenticate, if you are using this within the web interface and the user is logged in, the API is also accessible,
since they share the same cookie/session.

However, if you are building an external client and want to authenticate manually
you have to send your credentials ``username`` and ``password`` as
POST parameter to ``http://pyload-core/api/login``.

The result will be your session id. If you are using cookies, it will be set and you can use the API now.
In case you don't have cookies enabled you can pass the session id as ``session`` POST parameter
so pyLoad can authenticate you.


Calling Methods
---------------

In general you can use any method listed at the :class:`Api <module.Api.Api>` documentation, which is also available to
the thrift backend.

Access works simply via ``http://pyload-core/api/methodName``, where ``pyload-core`` is the ip address
or hostname including the web interface port. By default on local access this would be `localhost:8000`.

The return value will be formatted in JSON, complex data types as dictionaries. Definition for data types can be found
:doc:`here <datatypes>`

Passing parameters
------------------

To pass arguments you have two choices:
Either use positional arguments, e.g.: ``http://pyload-core/api/getFileData/1``, where 1 is the FileID, or use keyword
arguments supplied via GET or POST ``http://pyload-core/api/getFileData?fid=1``. You can find the argument names
in the :class:`Api <module.Api.Api>` documentation.

It is important that *all* arguments are in JSON format. So ``http://pyload-core/api/getFileData/1`` is valid because
1 represents an integer in json format. On the other hand if the method is expecting strings, this would be correct:
``http://pyload-core/api/getUserData/"username"/"password"``.

Strings are wrapped in double qoutes, because `"username"` represents a string in JSON format. It's not limited to
strings and integers, every container type like lists and dicts are possible. You usually don't have to convert them.
Just use a JSON encoder before using them in the HTTP request.

Please note that the data has to be urlencoded at last. (Most libraries will do that automatically)


.. rubric:: Footnotes

.. [1] http://de.wikipedia.org/wiki/JavaScript_Object_Notation