from django.contrib import admin
from .models import Album, Photo, Client


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')
    search_fields = ('title',)


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ('title', 'album', 'is_featured', 'created_at')
    list_filter = ('album', 'is_featured')
    search_fields = ('title',)
    list_editable = ('is_featured',)


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'preferred_date', 'preferred_time', 'created_at')
    search_fields = ('name', 'email', 'phone')
    list_filter = ('preferred_date',)