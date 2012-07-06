# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
from django.db import models
from django.utils.translation import ugettext_lazy as _


class Category(models.Model):
    """
    A category of KML resources, for example "Bathymetrie" or "Kustlijnen".
    One Category contains many KmlResource's.
    """

    name = models.CharField(
        db_column='name',
        verbose_name=_('name'),
        max_length=40,
        null=False, blank=False,
        help_text=_('category_name_help_text')
    )
    description = models.TextField(
        db_column='description',
        verbose_name=_('description'),
        null=True, blank=True,
        help_text=_('category_description_help_text')
    )

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        ordering = ('name', )
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')

KML_RESOURCE_CHOICES = [
    ('static', _('Static')),
    ('dynamic', _('Dynamic')),
    ('wms', _('WMS'))
]

class KmlResource(models.Model):
    """
    A resource can be a dynamic KML (generated by the server) or static KML, in which case
    we only need to URL to the KML file.
    A KmlResource belongs to one Category.
    """

    name = models.CharField(
        db_column='name',
        verbose_name=_('name'),
        max_length=80,
        null=False, blank=False,
        help_text=_('kml_resource_name_help_text')
    )
    description = models.TextField(
        db_column='description',
        verbose_name=_('description'),
        null=True, blank=True,
        help_text=_('kml_resource_description_help_text')
    )
    category = models.ForeignKey('Category', verbose_name=_('Category'), null=False, blank=False)
    # is_dynamic indicates whether to actually use the url ...
    # not quite BCNF but that's not really relevant with such a tiny domain model
    url = models.CharField(
        db_column='url',
        verbose_name=_('URL'),
        max_length=500, blank=True, null=True,
        help_text=_('url_help_text')
    )
    #is_dynamic = models.BooleanField(
    #    db_column='is_dynamic',
    #    verbose_name=_('dynamic'),
    #    help_text=_('is_dynamic_help_text')
    #)
    kml_type = models.CharField(
        db_column='kml_type',
        verbose_name=_('type'),
        null=False, blank=False,
        max_length=20,
        choices=KML_RESOURCE_CHOICES,
        help_text=_('kml_type_help_text')
    )
    slug = models.SlugField(
        db_column='slug',
        verbose_name=_('system name'),
        null=True, blank=True,
        help_text=_('slug_help_text')
    )
    preview_image = models.FileField(
        db_column='preview_image',
        verbose_name=_('preview image'),
        upload_to='uploaded_preview_images', max_length=500,
        help_text=_('preview_image_help_text'),
        null=True, blank=True
    )

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        ordering = ['name']
        verbose_name = _('KML resource')
        verbose_name_plural = _('KML resources')
