from django.contrib import admin
from .models import Filiere, Module


class ModuleInline(admin.TabularInline):
    model = Module
    extra = 2


@admin.register(Filiere)
class FiliereAdmin(admin.ModelAdmin):
    list_display = ('nom', 'duree', 'ordre', 'actif')
    list_editable = ('ordre', 'actif')
    prepopulated_fields = {'slug': ('nom',)}
    inlines = [ModuleInline]
