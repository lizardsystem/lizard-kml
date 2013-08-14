lizard-kml
==========

Keyhole Markup Language support for Lizard using the Google Earth plugin.

Running the application
-----------------------

Install the dependencies::

   $> sudo apt-get install python-psycopg2 python-matplotlib python-pyproj wget

Install build dependencies::

   $> sudo apt-get install libatlas-base-dev gfortran g++ libz-dev libpng-dev libfreetype6-dev python-dev liblapack-dev

Install some more dependencies, might want to use a virtualenv. These packages are incompatible with buildout.
They refer to run-time dependencies in their setup.py, which are unavailable at "build-time".
The packages for this in your Ubuntu repositories are probably too old.

   $> easy_install numpy scipy netCDF4 pandas pytz python-dateutil six

Initialize the Python interpreter paths::

    $> python bootstrap.py

Download and build the dependencies::

    $> bin/buildout

The following command creates the tables in a local SQLite DB::

    $> bin/django syncdb

Update the tables::

    $> bin/django migrate

Load some test KMLs (fixture)::

    $> bin/django loaddata lizard_kml

Run the internal webserver::

    $> bin/django runserver host:port

All set, point your browser to http://host:port/.

Doing some more
---------------

Need a local mirror of the NetCDF files? Free up approx. 3 GB of space and use this management command::

    $> bin/django sync_netcdfs

This script uses ``wget``, which should be available everywhere.

You might want to install the right fonts for matplotlib as well::

    $> sudo apt-get install libsys-cpu-perl pcf2bdf tex-gyre ttf-bitstream-vera tv-fonts xfonts-traditional
