from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('love_stories/', views.weddings, name='weddings'),
    path('portraits/', views.portraits, name='portraits'),
    path('events/', views.events, name='events'),
    path('about/', views.about, name='about'),
    path('booking/', views.booking, name='booking'),

    # Photographer gallery manager
    # Specific paths must come BEFORE <slug:slug>, otherwise
    # "reorder" / "showcase" are captured as slugs.
    path('client-galleries/', views.gallery_manager, name='gallery_manager'),
    path('client-galleries/new/', views.gallery_create, name='gallery_create'),
    path('client-galleries/reorder/', views.client_galleries_reorder, name='client_galleries_reorder'),
    path('client-galleries/showcase/reorder/', views.showcase_reorder, name='showcase_reorder'),
    path('client-galleries/photo/<int:photo_id>/delete/', views.gallery_delete_photo, name='gallery_delete_photo'),
    path('client-galleries/<slug:slug>/reorder/', views.gallery_reorder, name='gallery_reorder'),
    path('client-galleries/<slug:slug>/layout/', views.gallery_layout, name='gallery_layout'),
    path('client-galleries/<slug:slug>/', views.gallery_edit, name='gallery_edit'),

    # Public gallery
    path('gallery/<slug:slug>/', views.client_gallery, name='client_gallery'),
    path('gallery/<slug:slug>/download-all/', views.download_all_photos, name='download_all_photos'),
]
