# ============================================================
# ВСТАВ ЦЕ В views.py ЗАМІСТЬ ОБОХ def home(request):
# Імпорти зверху файлу не міняй.
# ============================================================

def _home_gallery_photos(gallery, limit=None):
    """Same order as on the gallery edit page."""
    if not gallery:
        return []

    items = list(
        gallery.showcase_items.select_related('photo').order_by('order', 'id')
    )
    photos = [item.photo for item in items if item.photo_id and getattr(item.photo, 'image', None)]

    if not photos:
        photos = [p for p in gallery.photos.all().order_by('order', 'id') if p.image]

    if limit is not None:
        return photos[:limit]
    return photos


def home(request):
    form_sent = False

    if request.method == 'POST' and request.POST.get('inquiry') == '1':
        name = (request.POST.get('name') or '').strip()
        phone = (request.POST.get('phone') or '').strip()
        instagram = (request.POST.get('instagram') or '').strip()
        details = '\n'.join(filter(None, [
            request.POST.get('shoot_type'),
            request.POST.get('preferred_date'),
            request.POST.get('hours'),
            request.POST.get('vibe'),
            request.POST.get('camera_comfort'),
            request.POST.get('location'),
            request.POST.get('stood_out'),
            request.POST.get('pinterest'),
            request.POST.get('details'),
            f'Instagram: {instagram}' if instagram else '',
            request.POST.get('preferred_contact'),
        ]))
        Client.objects.create(
            name=name or 'Inquiry',
            email='inquiry@vas.photo.nyc',
            phone=phone,
            message=details,
        )
        form_sent = True

    carousel_gallery = (
        Album.objects.filter(title__iexact='Carousel').first()
        or Album.objects.filter(slug__iexact='carousel').first()
    )
    prices_gallery = (
        Album.objects.filter(title__iexact='Prices').first()
        or Album.objects.filter(slug__iexact='prices').first()
    )

    portfolio_galleries = (
        Album.objects.filter(
            showcase_category=Album.LOVE_STORIES,
            is_private=False,
        )
        .order_by('display_order', '-created_at')[:6]
    )

    return render(request, 'home.html', {
        'form_sent': form_sent,
        'carousel_photos': _home_gallery_photos(carousel_gallery, 40),
        'price_photos': _home_gallery_photos(prices_gallery, 4),
        'portfolio_galleries': portfolio_galleries,
    })
