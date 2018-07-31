cloudside: download, assess, and visualize weather data
=======================================================
.. image:: https://travis-ci.org/Geosyntec/cloudside.svg?branch=master
    :target: https://travis-ci.org/Geosyntec/cloudside

.. image:: https://coveralls.io/repos/phobson/cloudside/badge.svg?branch=master&service=github
  :target: https://coveralls.io/github/phobson/cloudside?branch=master




The problem this is solving
---------------------------

``cloudside`` is a library suited to parsing weather data in the METAR
format. METAR is kind of a mess and not very human-readable. Hopefully
this makes things a bit easier. What appears to be an official spec on the
format can be found here_.

.. _here: https://www.ncdc.noaa.gov/wdcmet/data-access-search-viewer-tools/us-metar-program-overview


Basically I wanted a library that could do something like this:

.. code:: python

    import cloudside
    data = cloudside.asos.get_data('KPDX', '2012-12-01', '2015-05-01')
    fig = cloudside.viz.rose(data)

And so ``cloudside`` does that.

Basic History
-------------

`Tom Pollard <https://github.com/tomp/python-metar>`_ originally wrote ``python-metar`` to parse weather hourly reports as they were posted to the web.
Building on top of his original work, ``cloudside`` tries to provide an easy way to download and visualize data from ASOS.

You can download ``cloudside`` from the repoository from Github_.

.. _Github: https://github.com/phobson/cloudside

Dependencies
------------
* Python 3.5 or greater
* recent versions of pandas, matplotlib
* python-metar to actually parse the metar codes
* Jupyter for running notebook-based examples (optional)
* pytest for testing (optional)
* sphinx to build the documentation (optional)

If you're using `environments <http://conda.pydata.org/docs/intro.html>`_
managed through ``conda`` (recommended), this will
get you started: ::

    conda create --name=cloudside python=3.6 notebook pytest pandas matplotlib requests coverage

Followed by: ::

    source activate cloudside # (omit "source" on Windows)

Installation
------------

* Activate your ``conda`` environment;
* Install python-metar from Github
* Clone my fork from Github;
* Change to that resulting directory;
* Install via pip; and
* Back out of that directory to use

::

    source activate cloudside # (omit "source" on Windows)
    pip install git+https://github.com/tomp/python-metar.git
    git clone https://github.com/phobson/cloudside.git
    cd cloudside
    pip install .
    cd ../..


Testing
-------

Tests are run via ``pytest``. Run them all with: ::

    source activate cloudside # (omit "source" on Windows)
    python -c "import cloudside; cloudside.test()"

Documentation
-------------
We have `HTML docs built with sphinx <http://phobson.github.io/cloudside/>`_.

Development status
------------------
This is sort of a weekend hack.
But I keep adding stuff to it.
So, uh, *caveat emptor*, I guess.
