from django.contrib import admin
from .models import Album, Photo


class PhotoInline(admin.TabularInline):
    model = Photo
    extra = 3


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ('titre', 'ordre', 'date', 'actif')
    list_editable = ('ordre', 'actif')
    prepopulated_fields = {'slug': ('titre',)}
    inlines = [PhotoInline]
