.. _overview:

=======================================
API - Application Programming Interface
=======================================

From Wikipedia, the free encyclopedia [1]_:

    An application programming interface (API) is a source code based specification intended to be used as an interface
    by software components to communicate with each other. An API may include specifications for routines,
    data structures, object classes, and variables.

.. rubric:: Motivation

The idea of the centralized pyLoad :class:`Api <pyload.api.Api>` is to give uniform access to all integral parts
and plugins in pyLoad as well as other clients written in arbitrary programming languages.
Most of the :class:`Api <pyload.api.Api>` functionality is exposed via HTTP or WebSocktes [2]_ as
simple JSON objects [3]_. In conclusion the :class:`Api <pyload.api.Api>` is accessible via many programming languages,
over network from remote machines and over browser with javascript.


.. rubric:: Contents

.. toctree::

    json_api.rst
    websocket_api.rst
    components.rst
    datatypes.rst


.. rubric:: Footnotes

.. [1] http://en.wikipedia.org/wiki/Application_programming_interface
.. [2] http://en.wikipedia.org/wiki/WebSocket
.. [3] http://en.wikipedia.org/wiki/Json
