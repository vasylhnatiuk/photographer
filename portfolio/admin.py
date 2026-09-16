from django.contrib import admin
from .models import Album, Photo, ShowcasePhoto, Client


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'gallery_type',
        'showcase_category',
        'display_order',
        'is_private',
        'created_at',
    )

    list_filter = (
        'gallery_type',
        'showcase_category',
        'is_private',
    )

    search_fields = (
        'title',
        'client_name',
        'slug',
    )

    ordering = (
        'gallery_type',
        'display_order',
        '-created_at',
    )

    list_editable = (
        'gallery_type',
        'display_order',
    )

    prepopulated_fields = {
        'slug': ('title',),
    }


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'album',
        'order',
        'is_featured',
        'created_at',
    )

    list_filter = (
        'album',
        'is_featured',
    )

    search_fields = (
        'title',
        'album__title',
    )

    ordering = (
        'album',
        'order',
        'id',
    )


@admin.register(ShowcasePhoto)
class ShowcasePhotoAdmin(admin.ModelAdmin):
    list_display = (
        'album',
        'photo',
        'order',
    )

    list_filter = (
        'album',
    )

    ordering = (
        'album',
        'order',
    )


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'email',
        'phone',
        'preferred_date',
        'preferred_time',
        'created_at',
    )

    search_fields = (
        'name',
        'email',
        'phone',
    )

    ordering = (
        '-created_at',
    )