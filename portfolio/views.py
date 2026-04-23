from django.shortcuts import render, redirect
from .models import Photo, Album, Client


# 🏠 HOME
def home(request):
    featured_photos = Photo.objects.filter(is_featured=True)[:6]
    return render(request, 'home.html', {
        'featured_photos': featured_photos
    })


# 📸 GALLERY
def gallery(request):
    photos = Photo.objects.all().order_by('-created_at')
    return render(request, 'portraits.html', {
        'photos': photos
    })


# 🗂 ALBUMS
def albums(request):
    albums = Album.objects.all()
    return render(request, 'weddings.html', {
        'albums': albums
    })

def weddings(request):
    return render(request, "weddings.html")

def portraits(request):
    return render(request, "portraits.html")


# 👤 ABOUT
def about(request):
    return render(request, 'about.html')


# 📩 BOOKING / CLIENT FORM
def booking(request):
    if request.method == 'POST':
        Client.objects.create(
            name=request.POST.get('name'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone'),
            preferred_date=request.POST.get('preferred_date'),
            preferred_time=request.POST.get('preferred_time'),
            message=request.POST.get('message')
        )
        return redirect('home')

    return render(request, 'booking.html')