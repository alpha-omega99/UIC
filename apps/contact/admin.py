from django.contrib import admin
from .models import MessageContact


@admin.register(MessageContact)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'email', 'lu', 'created_at')
    list_editable = ('lu',)
    list_filter = ('lu', 'sujet')
    search_fields = ('prenom', 'nom', 'email', 'message')
    readonly_fields = ('created_at',)
