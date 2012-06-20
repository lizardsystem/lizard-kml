from tastypie import fields
from tastypie.resources import ModelResource, ALL, ALL_WITH_RELATIONS

from lizard_kml.models import Category, KmlResource


class CategoryResource(ModelResource):
    class Meta:
        queryset = Category.objects.all()
        list_allowed_methods = ['get']
        excludes = []

class KmlSourceResource(ModelResource):
    category = fields.ForeignKey(CategoryResource, 'category')

    class Meta:
        queryset = KmlResource.objects.all()
        list_allowed_methods = ['get']
        excludes = []
