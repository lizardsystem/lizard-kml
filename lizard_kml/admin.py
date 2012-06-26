from django.contrib import admin
from django import forms
from django.utils.translation import ugettext_lazy as _

from lizard_kml.models import Category, KmlResource

def pass_help_text(Model, field_name):
    return Model._meta.get_field_by_name(field_name)[0].help_text

class KmlResourceForm(forms.ModelForm):
    class Meta:
        model = KmlResource
        fields = ['name', 'description', 'category', 'url', 'is_dynamic', 'slug', 'preview_image']
        widgets = {
            'name': forms.TextInput(attrs={'size': 100}),
            'description': forms.Textarea(attrs={'rows': 5, 'cols': 50}),
            'url': forms.TextInput(attrs={'size': 100})
        }

class KmlResourceAdmin(admin.ModelAdmin):
    model = KmlResource
    list_display = ['name', 'category', 'url', 'slug']
    fields = ['name', 'description', 'category', 'url', 'is_dynamic', 'slug', 'preview_image']
    form = KmlResourceForm

class KmlResourceInlineForm(forms.ModelForm):
    class Meta:
        fields = ['name', 'url', 'category', 'slug']
        widgets = {
            'name': forms.TextInput(attrs={'size': 50}),
            'description': forms.Textarea(attrs={'rows': 4, 'cols': 30}),
            'url': forms.TextInput(attrs={'size': 50})
        }

class KmlResourceInline(admin.TabularInline):
    model = KmlResource
    ordering = ['name']
    extra = 0
    can_delete = False
    form = KmlResourceInlineForm

class CategoryAdmin(admin.ModelAdmin):
    model = Category
    fields = ['name', 'description']
    inlines = [KmlResourceInline]

admin.site.register(Category, CategoryAdmin)
admin.site.register(KmlResource, KmlResourceAdmin)
