lizard-kml
==========================================

Keyhole Markup Language support for Lizard using the Google Earth plugin.

Symlink a buildout configuration
--------------------------------

Initially, there's no ``buildout.cfg``. You need to make that a symlink to the
correct configuration. On your development machine, that is
``development.cfg`` (and ``staging.cfg`` or ``production.cfg``, for instance
on the server)::

    $> ln -s development.cfg buildout.cfg
