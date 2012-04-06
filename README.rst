lizard-kml
==========================================

Keyhole Markup Language support for Lizard using the Google Earth plugin.

Running the application
--------------------------------

Initially, there's no ``buildout.cfg``. You need to make that a symlink to the
correct configuration. On your development machine, that is
``development.cfg`` (and ``staging.cfg`` or ``production.cfg``, for instance
on the server)::

    $> ln -s development.cfg buildout.cfg

Next, download and build the dependencies:

    $> bin/buildout

Next, setup a postgres db, with a postgis template, using the settings in ``developmentsettings.py``.
Create the tables:

    $> bin/django syncdb
    $> bin/django migrate

Load some testdata (fixture):

    $> bin/django loaddata lizard_kml_open_kml_data

Run the internal webserver:

    $> bin/django runserver host:port

Point your browser to http://host:port/kml/viewer/