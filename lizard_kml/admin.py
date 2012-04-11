from django.contrib import admin

from lizard_kml.models import KmlType, Area

class KmlTypeAdmin(admin.ModelAdmin):
    model = KmlType

class AreaAdmin(admin.ModelAdmin):
    model = Area

admin.site.register(KmlType, KmlTypeAdmin)
admin.site.register(Area, AreaAdmin)
