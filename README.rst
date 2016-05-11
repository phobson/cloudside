cloudside: download, assess, and visualize weather data
=======================================================
.. image:: https://travis-ci.org/Geosyntec/cloudside.svg?branch=master
    :target: https://travis-ci.org/Geosyntec/cloudside

.. image:: https://coveralls.io/repos/phobson/cloudside/badge.svg?branch=master&service=github
  :target: https://coveralls.io/github/phobson/cloudside?branch=master




The problem this is solving
---------------------------

TBD

.. code:: python

    import cloudside
    data = cloudside.getASOSData('KPDX', '2012-12-01', '2015-05-01')
    fig = cloudside.viz.windrose(data)


Documentation
-------------
We have `HTML docs built with sphinx <http://phobson.github.io/cloudside/>`_.

Installation
------------
Binaries are available through my conda channel

``conda install --channel=phobson cloudside``

This is a pure python package, so installation from source should be as easy as running
``pip install .`` from the source directory if you've cloned the repo.

Otherwise, I think ``pip install git+https://github.com/phobson/cloudside.git`` will work.
(I'll upload to pip after this has sat around for a while.

Development status
------------------
This is sort of a weekend hack. So, uh, *caveat emptor*, I guess.
