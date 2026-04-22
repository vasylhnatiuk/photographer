from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path("weddings/", views.weddings, name="weddings"),
    path("portraits/", views.portraits, name="portraits"),
    path('albums/', views.albums, name='albums'),
    path('about/', views.about, name='about'),
    path('booking/', views.booking, name='booking'),
]