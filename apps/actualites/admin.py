from django.contrib import admin
from .models import Article, Categorie


@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    pass


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('titre', 'categorie', 'date_publication', 'publie')
    list_editable = ('publie',)
    list_filter = ('publie', 'categorie')
    search_fields = ('titre', 'contenu')
    prepopulated_fields = {'slug': ('titre',)}
