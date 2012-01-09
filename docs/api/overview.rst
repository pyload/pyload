.. _overview:

=======================================
API - Application Programming Interface
=======================================

From Wikipedia, the free encyclopedia [1]_:

    An application programming interface (API) is a source code based specification intended to be used as an interface
    by software components to communicate with each other. An API may include specifications for routines,
    data structures, object classes, and variables.

.. rubric:: Motivation

The idea of the centralized pyLoad :class:`Api <module.Api.Api>` is to give uniform access to all integral parts
and plugins in pyLoad, and furthermore to other clients, written in arbitrary programming languages.
Most of the :class:`Api <module.Api.Api>` functionality is exposed via RPC [2]_ and accessible via thrift [3]_ or
simple JSON objects [4]_. In conclusion the :class:`Api <module.Api.Api>` is accessible via many programming language,
over network from remote maschines and over browser with javascript.


.. rubric:: Contents

.. toctree::

    thrift_api.rst
    json_api.rst
    datatypes.rst


.. rubric:: Footnotes

.. [1] http://en.wikipedia.org/wiki/Application_programming_interface
.. [2] http://en.wikipedia.org/wiki/Remote_procedure_call
.. [3] `<http://en.wikipedia.org/wiki/Thrift_(protocol)>`_
.. [4] http://en.wikipedia.org/wiki/Json