.. _json_api:

========
JSON API
========

JSON [1]_ is a lightweight object notation and wrappers exists for nearly every programming language. Every
modern browser is able to load JSON objects with JavaScript. Unlike other RPC methods you do not need to generate or precompile
any stub methods. The JSON :class:`Api <pyload.api.Api>` is ready to be used in most languages and most JSON libraries are lightweight
enough to build very small and performant scripts. Because of the builtin support, JSON is the first choice for all browser
applications.

Login
-----

First you need to authenticate, if you are using this within the web interface and the user is logged in, the API is also accessible,
since they share the same cookie/session.

However, if you are building an external client and want to authenticate manually
you have to send your credentials ``username`` and ``password`` as
POST parameter to ``http://pyload-core/api/login``.

The result will be your session id. If you are using cookies, it will be set and you can use the API now.
In case you do not have cookies enabled you can pass the session id as ``session`` POST parameter
so pyLoad can authenticate you.


Calling Methods
---------------

In general you can use any method listed at the :class:`Api <pyload.api.Api>` documentation, which is also available to
the thrift backend.

Access works simply via ``http://pyload-core/api/methodName``, where ``pyload-core`` is the ip address
or hostname including the web interface port. By default on local access this would be `localhost:8010`.

The return value will be formatted in JSON, complex data types as dictionaries. Definition for data types can be found
:doc:`here <datatypes>`

Passing parameters
------------------

To pass arguments you have two choices:
Either use positional arguments, e.g.: ``http://pyload-core/api/getFileData/1``, where 1 is the FileID, or use keyword
arguments supplied via GET or POST ``http://pyload-core/api/getFileData?fid=1``. You can find the argument names
in the :class:`Api <pyload.api.Api>` documentation.

It is important that *all* arguments are in JSON format. So ``http://pyload-core/api/getFileData/1`` is valid because
1 represents an integer in json format. On the other hand if the method is expecting strings, this would be correct:
``http://pyload-core/api/getUserData/"username"/"password"``.

Strings are wrapped in double qoutes, because `"username"` represents a string in JSON format. It's not limited to
strings and integers, every container type like lists and dicts are possible. You usually do not have to convert them.
Just use a JSON encoder before using them in the HTTP request.

Please note that the data has to be urlencoded at last. (Most libraries will do that automatically)

Example
-------

Here is a little python script that is able to send commands to the pyload api::

    # -*- coding: utf-8 -*-

    from urllib import urlopen, urlencode
    from json import dumps

    URL = "http://localhost:8010/api/{}"

    def login(user, pw):
        params = {"username": user, "password": pw}
        ret = urlopen(URL.format("login"), urlencode(params))
        return ret.read().strip("\"")

    # send arbitrary command to pyload api, parameter as keyword argument
    def send(session, command, **kwargs):
        # convert arguments to json format
        params = dict((k, dumps(v)) for k, v in kwargs.items())
        params['session'] = session
        ret = urlopen(URL.format(command), urlencode(params))
        return ret.read()

    if __name__ == "__main__":
        session = login("User", "pwhere")
        print("Session id:", session)

        result = send(session, "setCaptchaResult", tid=0, result="some string")
        print(result)



.. rubric:: Footnotes

.. [1] http://de.wikipedia.org/wiki/JavaScript_Object_Notation
