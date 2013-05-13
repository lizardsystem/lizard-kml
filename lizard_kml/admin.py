from django.contrib import admin
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse

from lizard_kml.models import Category, KmlResource

def pass_help_text(Model, field_name):
    return Model._meta.get_field_by_name(field_name)[0].help_text

class KmlResourceForm(forms.ModelForm):
    class Meta:
        model = KmlResource
        fields = ['name', 'description', 'category', 'url', 'kml_type', 'slug', 'preview_image', 'sorting_index']
        widgets = {
            'name': forms.TextInput(attrs={'size': 100}),
            'description': forms.Textarea(attrs={'rows': 5, 'cols': 50}),
            'url': forms.TextInput(attrs={'size': 100})
        }

class KmlResourceAdmin(admin.ModelAdmin):
    model = KmlResource
    list_display = ['name', 'category', 'limited_url', 'kml_type', 'slug', 'sorting_index']
    fields = ['name', 'description', 'category', 'url', 'kml_type', 'slug', 'preview_image', 'sorting_index']
    ordering = ['category__sorting_index', 'sorting_index']
    form = KmlResourceForm

    def limited_url(self, obj):
        if len(obj.url) > 100:
            return obj.url[:100] + '[...]'
        return obj.url
    limited_url.short_description = 'URL'

class KmlResourceInlineForm(forms.ModelForm):
    class Meta:
        fields = ['name', 'url', 'category', 'kml_type', 'slug', 'sorting_index']
        widgets = {
            'name': forms.TextInput(attrs={'size': 50}),
            'description': forms.Textarea(attrs={'rows': 4, 'cols': 30}),
            'url': forms.TextInput(attrs={'size': 50})
        }

class KmlResourceInline(admin.TabularInline):
    model = KmlResource
    fields = ['name', 'url', 'category', 'kml_type', 'slug', 'deeplink', 'sorting_index']
    readonly_fields = ['deeplink']
    extra = 0
    ordering = ['name']
    can_delete = False
    form = KmlResourceInlineForm

    def deeplink(self, obj):
        url = reverse('admin:lizard_kml_kmlresource_change', args=(obj.id,))
        return '<a href="{0}"><b>Details</b></a>'.format(url)
    deeplink.allow_tags = True
    deeplink.short_description = 'Acties'

class CategoryAdmin(admin.ModelAdmin):
    model = Category
    list_display = ['name', 'collapsed_by_default', 'sorting_index']
    fields = ['name', 'description', 'collapsed_by_default', 'sorting_index']
    ordering = ['sorting_index']
    inlines = [KmlResourceInline]

admin.site.register(Category, CategoryAdmin)
admin.site.register(KmlResource, KmlResourceAdmin)
