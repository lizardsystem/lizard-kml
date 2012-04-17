from django.contrib import admin

from lizard_kml.models import Category, KmlResource

class CategoryAdmin(admin.ModelAdmin):
    model = Category

class KmlResourceAdmin(admin.ModelAdmin):
    model = KmlResource

admin.site.register(Category, CategoryAdmin)
admin.site.register(KmlResource, KmlResourceAdmin)
