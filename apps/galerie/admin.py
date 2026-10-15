from django.contrib import admin
from .models import Album, Photo


class PhotoInline(admin.TabularInline):
    model = Photo
    extra = 3


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ('titre', 'date', 'actif')
    prepopulated_fields = {'slug': ('titre',)}
    inlines = [PhotoInline]
