# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
from django.db import models
from django.utils.translation import ugettext_lazy as _

class KmlType(models.Model):
    """
    A category of KML files, for example "Jarkusprofielen" or "Vaklodingen".
    One KmlType contains KML files for many Area's.
    """

    name = models.CharField(_('name'), max_length=40)
    description = models.TextField(_('description'), null=True, blank=True)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        ordering = ('name', )

class Area(models.Model):
    """
    An area, for example "Walcheren" or "Maasvlakte", and an URL to its corresponding KML file.
    """

    name = models.CharField(_('name'), max_length=40)
    description = models.TextField(_('description'), null=True, blank=True)
    url = models.CharField(_('url'), max_length=200, blank=True, null=True)
    kml_type = models.ForeignKey('KmlType', null=True, blank=True)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        ordering = ('name', )
