lizard-kml
==========================================

Keyhole Markup Language support for Lizard using the Google Earth plugin.

Running the application
--------------------------------

Download and build the dependencies:

    $> bin/buildout

The following command creates the tables in a local SQLite DB:

    $> bin/django syncdb

Update the tables:

    $> bin/django migrate

Load some testdata (fixture):

    $> bin/django loaddata lizard_kml_open_kml_data

Run the internal webserver:

    $> bin/django runserver host:port

All set, point your browser to http://host:port/kml/viewer/