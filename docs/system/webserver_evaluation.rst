.. _webserver_evaluation:

====================
Webserver Evaluation
====================

pyLoad supports all kind of webserver that are usable with bottle.py [1]_.
For this reason we evaluted each of them to find the ones that are worth to be supported in pyLoad. The results of this
evaluation make sure pyload can select the most suited webserver with its auto selecting algorithm.

First selection
---------------

The first step was to take a short look at every webserver. For some it was not needed to further inspect them,
since they do not meet our requirements.

================== ==================================================================
Disregarded server Reason
================== ==================================================================
paste              threaded server, no improvement to bundled one
twisted            Too heavy (30 MiB RAM min), far more complex as what we need
diesel             Problems with setup, no default packages, Not working in tests
gunicorn           Preforking server, messes many things up in our use-case
gevent             Not usuable with several threads
gae                Google App Engine, not for personal maschines
rocket             threaded server, seems not better than bundled one
waitress           no large improvement to bundled threaded
================== ==================================================================

pyLoad has an threaded server bundled itself. All threaded server that were tested seems not better than this
implementation and thus were not further benchmarked. "flup", known as "fastcgi" in pyload, serves a different
use-case and is not taken into consideration here.

Comparision
-----------

The remaining servers, were evaluated for different criteria. We ran the following benchmark with different options:

    ab -n 15000 -c 1 http://127.0.0.1:8010/login

This benchmark was ran with -c 1, -c 5, as well as -k option to test performance with more concurrency and keep-alive
feature, we use time per request (mean, across all concurrent requests) for comparision.

Additionally we collected RAM usage statistic before (b.) (only 2-3 pages retrieved) and after (a.) the benchmarks were run.
The comparision also includes some notes and available packages or features, especially SSL is of interest.

========== ======== ======== ====== ====== ======= ======= === ============= ================================
Server     RAM (b.) RAM (a.) -c 1   -c 5   -c 1 -k -c 5 -k SSL Packages      Notes
========== ======== ======== ====== ====== ======= ======= === ============= ================================
wsgiref    21.7     22.6     1.240  1.179  1.312   1.513   No  Included
threaded   25.5     28.0     0.912  1.139  0.656   0.784   Yes Included
tornado    23.8     25.9     0.874  0.935  -       -       Yes mac,deb,arch
                                                               freebsd
fapws3     22.3     23.8     0.740  0.733  0.786   0.594   No  pip           Very reliable under load,
                                                                             problem with shutdown, will
                                                                             need patches for integration
meinheld   22.3     23.7     0.622  1.001  1.076   1.388   Yes pip           Segfaults when shutdown
eventlet   25.0     26.0     1.021  1.031  0.755   0.740   Yes mac,deb       Struggles a bit under load
                                                               freebsd       More ram with -k (27.6)

bjoern     21.7     23.2     0.623  0.513  -       -       No  git, freebsd  memory-leak with faulty -k
                                                                             packages out of date
========== ======== ======== ====== ====== ======= ======= === ============= ================================

"wsgiref" is a standard implementation shipped with python and within pyLoad known as builtin.
"threaded" is taken from cherryPy and also included with pyLoad.
The keep-alive implementation of "ab" is not 100% compliant, some server struggle with it.

Conclusion
----------

The wsgiref server is known to show strange performance on some system and is therefore not selected by default anymore.
The included threaded server has all needed functions, including SSL, and is usable without any other packages.
Threaded will be selected in case none of the other server is installed.

Our auto-select will favor RAM usage over performance too choose the most lightweight server as possible.
Activating SSL will decrease the options, many lightweight servers do not include SSL by choice.
They suggest tools like pound [2]_, stunnel [3]_, or any other reverse proxy capable server. Also these that are capable
of SSL suggest using other tools, their SSL performance was not tested here.

pyLoad will select a server in following order:
fapws3 -> meinheld -> bjoern -> tornado -> eventlet

.. rubric:: Footnotes

.. [1] https://bitbucket.org/spoob/pyload/src/127adb41465712548949ea872a5453e4b0b0fbb8/module/lib/bottle.py?at=default#cl-2555
.. [2] http://www.apsis.ch/pound/
.. [3] https://www.stunnel.org/index.html
