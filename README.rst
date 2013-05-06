lizard-kml
==========

Keyhole Markup Language support for Lizard using the Google Earth plugin.

Running the application
-----------------------

Install the dependencies::

   $> sudo apt-get install python-psycopg2 python-matplotlib python-pyproj

Install build dependencies::

   $> sudo apt-get install libatlas-base-dev gfortran libz-dev libpng-dev libfreetype6-dev python-dev

Install some more dependencies, might want to use a virtualenv::

   $> easy_install scipy numpy statsmodels # or pip

Initialize the Python interpreter paths::

    $> python bootstrap.py

Download and build the dependencies::

    $> bin/buildout

The following command creates the tables in a local SQLite DB::

    $> bin/django syncdb

Update the tables::

    $> bin/django migrate

Load some testdata (fixture)::

    $> bin/django loaddata lizard_kml

Run the internal webserver::

    $> bin/django runserver host:port

All set, point your browser to http://host:port/.

Doing some more
---------------

Need a local mirror of the NetCDF files? Free up approx. 3 GB of space and use this management command::

    $> bin/django sync_netcdfs
