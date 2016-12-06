.. _overview:

================
Extending pyLoad
================

.. pull-quote::
    Any sufficiently advanced technology is indistinguishable from magic.

    -- Arthur C. Clarke


.. rubric:: Motivation

pyLoad offers a comfortable and powerful plugin system to make extensions possible. With it you only need to have some
python knowledge and can just start right away writing your own plugins. This document gives you an overview about the
conceptual part. You should not leave out the :doc:`Base <base_plugin>` part, since it contains basic functionality for all plugin types.
A class diagram visualizing the relationship can be found below [1]_

.. rubric:: Contents

.. toctree::

    base_plugin.rst
    crypter_plugin.rst
    hoster_plugin.rst
    account_plugin.rst
    addon_plugin.rst


.. rubric:: Footnotes

.. [1] :ref:`plugin_hierarchy`
