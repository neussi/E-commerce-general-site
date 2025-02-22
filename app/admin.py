from django.contrib import admin
from .models import User, Product

# Enregistrement du modèle User avec un affichage personnalisé
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'phone', 'email', 'role')  # Affiche ces champs dans la liste des utilisateurs
    search_fields = ('username', 'phone', 'email')  # Permet de rechercher par ces champs

# Enregistrement du modèle User dans l'admin
admin.site.register(User, UserAdmin)


# Enregistrement du modèle Product
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'owner', 'created_at')
    search_fields = ('name', 'owner__username')
    list_filter = ('owner', 'created_at')

admin.site.register(Product, ProductAdmin)
