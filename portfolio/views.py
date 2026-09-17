import io
import json
import os
import zipfile

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import GalleryForm, PhotoUploadForm
from .models import Album, Photo, ShowcasePhoto


def home(request):
    return render(request, 'home.html')


def weddings(request):
    """
    Public gallery page.

    Shows:
    1. General / Selected Photos galleries grouped by category.
    2. Client galleries below them.
    """

    # GENERAL / SELECTED PHOTOS
    showcase_galleries = (
        Album.objects
        .filter(
            gallery_type=Album.SHOWCASE,
            is_private=False,
        )
        .prefetch_related('showcase_items__photo')
        .order_by('display_order', '-created_at')
    )

    grouped_sections = []

    for value, label in Album.SHOWCASE_CATEGORIES:
        category_galleries = [
            gallery
            for gallery in showcase_galleries
            if gallery.showcase_category == value
        ]

        grouped_sections.append({
            'value': value,
            'label': label,
            'galleries': category_galleries,
        })


    # CLIENT GALLERIES
    client_galleries = (
        Album.objects
        .filter(
            gallery_type=Album.CLIENT,
            is_private=False,
        )
        .prefetch_related('photos')
        .order_by('display_order', '-created_at')
    )


    return render(request, 'weddings.html', {
        'showcase_galleries': showcase_galleries,
        'grouped_sections': grouped_sections,
        'client_galleries': client_galleries,
    })




def portraits(request):
    return render(request, "portraits.html")


def events(request):
    return render(request, "events.html")


def about(request):
    return render(request, 'about.html')


def booking(request):
    return render(request, 'booking.html')


@login_required
def gallery_manager(request):
    client_galleries = (
        Album.objects.filter(gallery_type=Album.CLIENT)
        .prefetch_related('photos')
        .order_by('display_order', '-created_at')
    )
    showcase_galleries = (
        Album.objects.filter(gallery_type=Album.SHOWCASE)
        .prefetch_related('showcase_items__photo')
        .order_by('display_order', '-created_at')
    )
    return render(request, 'galleries/manager.html', {
        'client_galleries': client_galleries,
        'showcase_galleries': showcase_galleries,
    })


def _next_gallery_order(gallery_type):
    last = Album.objects.filter(gallery_type=gallery_type).order_by('-display_order').first()
    return (last.display_order + 1) if last else 0


@login_required
def gallery_create(request):
    if request.method == 'POST':
        form = GalleryForm(request.POST, request.FILES)
        if form.is_valid():
            gallery = form.save(commit=False)
            gallery.display_order = _next_gallery_order(gallery.gallery_type)
            if gallery.cover:
                gallery.cover._needs_optimization = True
            if gallery.love_stories_cover:
                gallery.love_stories_cover._needs_optimization = True
            gallery.save()

            # A general gallery is built from existing client-gallery photos.
            if gallery.is_showcase:
                selected_ids = _clean_id_list(request.POST.getlist('selected_photo_ids'))
                _save_showcase_selection(gallery, selected_ids)

            return redirect('gallery_edit', slug=gallery.slug)
    else:
        form = GalleryForm(initial={'gallery_type': Album.CLIENT})

    return render(request, 'galleries/form.html', {
        'form': form,
        'page_title': 'Create gallery',
    })


@login_required
def gallery_edit(request, slug):
    gallery = get_object_or_404(Album, slug=slug)
    all_client_photos = _all_photo_queryset() if gallery.is_showcase else Photo.objects.none()

    if request.method == 'POST':
        if 'save_gallery' in request.POST:
            form = GalleryForm(request.POST, request.FILES, instance=gallery)
            if form.is_valid():
                updated = form.save(commit=False)
                if 'cover' in request.FILES:
                    updated.cover._needs_optimization = True
                if 'love_stories_cover' in request.FILES:
                    updated.love_stories_cover._needs_optimization = True
                updated.save()

                if updated.is_showcase:
                    selected_ids = _clean_id_list(request.POST.getlist('selected_photo_ids'))
                    _save_showcase_selection(updated, selected_ids)
                else:
                    ShowcasePhoto.objects.filter(album=updated).delete()

                return redirect('gallery_edit', slug=updated.slug)

        elif 'upload_photos' in request.POST:
            upload_form = PhotoUploadForm(request.POST, request.FILES)
            if upload_form.is_valid():
                files = upload_form.cleaned_data.get('photos', [])
                start_order = gallery.photos.count()
                created = []
                for index, image in enumerate(files, start=start_order):
                    image._needs_optimization = True
                    created.append(Photo.objects.create(album=gallery, image=image, order=index))
                if gallery.is_showcase and created:
                    existing = list(
                        gallery.showcase_items.order_by('order', 'id').values_list('photo_id', flat=True)
                    )
                    _save_showcase_selection(gallery, existing + [photo.id for photo in created])
                return redirect('gallery_edit', slug=gallery.slug)
    else:
        form = GalleryForm(instance=gallery)

    form = locals().get('form', GalleryForm(instance=gallery))
    upload_form = PhotoUploadForm()
    selected_ids = list(
        gallery.showcase_items.order_by('order', 'id').values_list('photo_id', flat=True)
    ) if gallery.is_showcase else []
    if gallery.is_showcase:
        by_id = {photo.id: photo for photo in Photo.objects.filter(id__in=selected_ids)}
        selected_photos = [by_id[photo_id] for photo_id in selected_ids if photo_id in by_id]
    else:
        selected_photos = []

    return render(request, 'galleries/edit.html', {
        'gallery': gallery,
        'photos': gallery.photos.all(),
        'form': form,
        'upload_form': upload_form,
        'all_client_photos': all_client_photos,
        'selected_ids': selected_ids,
        'selected_photos': selected_photos,
    })


@login_required
def gallery_layout(request, slug):
    gallery = get_object_or_404(Album, slug=slug)
    if not gallery.is_showcase:
        return redirect('gallery_edit', slug=gallery.slug)

    library = list(_all_photo_queryset())
    by_id = {photo.id: photo for photo in library}
    slot_ids = _normalize_slots(gallery.layout_slots)
    if not any(slot_ids):
        existing = list(
            gallery.showcase_items.order_by('order', 'id').values_list('photo_id', flat=True)
        )
        slot_ids = _normalize_slots(existing)

    if request.method == 'POST':
        raw = request.POST.get('slots') or '[]'
        try:
            incoming = json.loads(raw)
        except json.JSONDecodeError:
            incoming = []
        slot_ids = _normalize_slots(incoming)
        gallery.layout_slots = slot_ids
        gallery.save(update_fields=['layout_slots'])
        filled = [photo_id for photo_id in slot_ids if photo_id]
        _save_showcase_selection(gallery, filled)
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'ok': True})
        return redirect('gallery_layout', slug=gallery.slug)

    rows = _layout_rows(slot_ids, by_id)
    return render(request, 'galleries/layout.html', {
        'gallery': gallery,
        'rows': rows,
        'library': library,
        'slot_ids': slot_ids,
        'slot_count': LAYOUT_SLOT_COUNT,
    })


def _client_photo_queryset():
    return (
        Photo.objects
        .filter(album__gallery_type=Album.CLIENT)
        .select_related('album')
        .order_by('album__display_order', 'album__title', 'order', 'id')
    )


def _all_photo_queryset():
    return (
        Photo.objects
        .select_related('album')
        .order_by('album__gallery_type', 'album__display_order', 'album__title', 'order', 'id')
    )


def _clean_id_list(values):
    result = []
    for value in values:
        try:
            value = int(value)
        except (TypeError, ValueError):
            continue
        if value not in result:
            result.append(value)
    return result


def _save_showcase_selection(gallery, photo_ids):
    """Replace showcase selection while preserving the exact submitted order."""
    allowed = set(
        Photo.objects.filter(id__in=photo_ids).values_list('id', flat=True)
    )
    ordered_ids = [photo_id for photo_id in photo_ids if photo_id in allowed]

    with transaction.atomic():
        ShowcasePhoto.objects.filter(album=gallery).delete()
        ShowcasePhoto.objects.bulk_create([
            ShowcasePhoto(album=gallery, photo_id=photo_id, order=position)
            for position, photo_id in enumerate(ordered_ids)
        ])


@login_required
@require_POST
def gallery_delete_photo(request, photo_id):
    photo = get_object_or_404(Photo, id=photo_id)
    gallery_slug = photo.album.slug
    photo.delete()
    return redirect('gallery_edit', slug=gallery_slug)


@login_required
@require_POST
def gallery_reorder(request, slug):
    gallery = get_object_or_404(Album, slug=slug)
    if not (gallery.is_client_gallery or gallery.is_showcase):
        return HttpResponseBadRequest('This gallery cannot be reordered here.')

    try:
        payload = json.loads(request.body)
        photo_ids = payload.get('photo_ids', [])
        if not isinstance(photo_ids, list):
            raise ValueError
    except (json.JSONDecodeError, ValueError):
        return HttpResponseBadRequest('Invalid photo order.')

    photo_ids = [int(x) for x in photo_ids]
    if gallery.is_showcase:
        allowed = set(
            gallery.showcase_items.filter(photo_id__in=photo_ids).values_list('photo_id', flat=True)
        )
        if set(photo_ids) != allowed:
            return HttpResponseBadRequest('Invalid photo list.')
        with transaction.atomic():
            for position, photo_id in enumerate(photo_ids):
                ShowcasePhoto.objects.filter(album=gallery, photo_id=photo_id).update(order=position)
    else:
        photos = list(gallery.photos.filter(id__in=photo_ids))
        by_id = {photo.id: photo for photo in photos}
        if len(photo_ids) != len(photos) or set(photo_ids) != set(by_id):
            return HttpResponseBadRequest('Invalid photo list.')
        with transaction.atomic():
            for position, photo_id in enumerate(photo_ids):
                Photo.objects.filter(id=photo_id, album=gallery).update(order=position)

    return JsonResponse({'ok': True})


@login_required
@require_POST
def showcase_reorder(request):
    try:
        payload = json.loads(request.body)
        gallery_ids = payload.get('gallery_ids', [])
        if not isinstance(gallery_ids, list):
            raise ValueError
    except (json.JSONDecodeError, ValueError):
        return HttpResponseBadRequest('Invalid gallery order.')

    galleries = list(Album.objects.filter(id__in=gallery_ids, gallery_type=Album.SHOWCASE))
    by_id = {gallery.id: gallery for gallery in galleries}
    if len(gallery_ids) != len(galleries) or set(gallery_ids) != set(by_id):
        return HttpResponseBadRequest('Invalid gallery list.')

    with transaction.atomic():
        for position, gallery_id in enumerate(gallery_ids):
            Album.objects.filter(id=gallery_id, gallery_type=Album.SHOWCASE).update(display_order=position)

    return JsonResponse({'ok': True})


@login_required
@require_POST
def client_galleries_reorder(request):
    try:
        payload = json.loads(request.body)
        gallery_ids = payload.get('gallery_ids', [])
        if not isinstance(gallery_ids, list):
            raise ValueError
    except (json.JSONDecodeError, ValueError):
        return HttpResponseBadRequest('Invalid gallery order.')

    galleries = list(Album.objects.filter(id__in=gallery_ids, gallery_type=Album.CLIENT))
    by_id = {gallery.id: gallery for gallery in galleries}
    if len(gallery_ids) != len(galleries) or set(gallery_ids) != set(by_id):
        return HttpResponseBadRequest('Invalid gallery list.')

    with transaction.atomic():
        for position, gallery_id in enumerate(gallery_ids):
            Album.objects.filter(id=gallery_id, gallery_type=Album.CLIENT).update(display_order=position)

    return JsonResponse({'ok': True})


LAYOUT_SLOT_COUNT = 40
LAYOUT_PATTERN = [3, 1, 2, 1]


def _kind_for_size(size):
    if size == 1:
        return 'big'
    if size == 2:
        return 'pair'
    return 'trio'


def _normalize_slots(raw, size=LAYOUT_SLOT_COUNT):
    slots = list(raw or [])
    cleaned = []
    for item in slots[:size]:
        try:
            cleaned.append(int(item) if item not in (None, '', 0) else None)
        except (TypeError, ValueError):
            cleaned.append(None)
    while len(cleaned) < size:
        cleaned.append(None)
    return cleaned


def _photos_from_slots(slot_ids):
    ids = [photo_id for photo_id in slot_ids if photo_id]
    by_id = {photo.id: photo for photo in Photo.objects.filter(id__in=ids)}
    photos = []
    for index, photo_id in enumerate(slot_ids):
        photo = by_id.get(photo_id)
        if not photo:
            continue
        photo.idx = len(photos)
        photo.slot = index
        photos.append(photo)
    return photos


def _layout_rows(slot_ids, photos_by_id=None):
    if photos_by_id is None:
        ids = [photo_id for photo_id in slot_ids if photo_id]
        photos_by_id = {photo.id: photo for photo in Photo.objects.filter(id__in=ids)}
    rows = []
    i = 0
    step = 0
    while i < len(slot_ids):
        size = LAYOUT_PATTERN[step % len(LAYOUT_PATTERN)]
        chunk_ids = slot_ids[i:i + size]
        cells = []
        for photo_id in chunk_ids:
            photo = photos_by_id.get(photo_id) if photo_id else None
            cells.append(photo)
        while len(cells) < size:
            cells.append(None)
        rows.append({'kind': _kind_for_size(size), 'cells': cells, 'start': i})
        i += size
        step += 1
    return rows


def _portrait_rows(photos):
    photos = list(photos)
    rows = []
    pattern = [3, 1, 2, 1]
    i = 0
    step = 0
    while i < len(photos):
        size = pattern[step % len(pattern)]
        chunk = photos[i:i + size]
        if len(chunk) == 1:
            kind = 'big'
        elif len(chunk) == 2:
            kind = 'pair'
        else:
            kind = 'trio'
        rows.append({'kind': kind, 'photos': chunk})
        i += len(chunk)
        step += 1
    return rows


def client_gallery(request, slug):
    gallery = get_object_or_404(Album, slug=slug)
    session_key = f'gallery_unlocked_{gallery.pk}'
    password_error = ''
    unlocked = (not gallery.is_private) or request.user.is_authenticated or request.session.get(session_key)

    if gallery.is_private and request.method == 'POST' and 'gallery_password' in request.POST:
        expected = (gallery.access_password or '1212').strip()
        given = (request.POST.get('gallery_password') or '').strip()
        if given == expected:
            request.session[session_key] = True
            return redirect('client_gallery', slug=gallery.slug)
        password_error = 'Wrong password.'

    layout_rows = None
    if gallery.is_showcase:
        slot_ids = _normalize_slots(gallery.layout_slots)
        if any(slot_ids):
            photos = _photos_from_slots(slot_ids)
            layout_rows = _layout_rows(slot_ids)
        else:
            items = gallery.showcase_items.select_related('photo', 'photo__album').order_by('order', 'id')
            photos = [item.photo for item in items]
            for index, photo in enumerate(photos):
                photo.idx = index
    else:
        photos = list(gallery.photos.all())
        for index, photo in enumerate(photos):
            photo.idx = index

    return render(request, 'galleries/client.html', {
        'gallery': gallery,
        'photos': photos,
        'rows': layout_rows or _portrait_rows(photos),
        'can_reorder': request.user.is_authenticated and unlocked and not layout_rows,
        'gallery_locked': gallery.is_private and not unlocked,
        'password_error': password_error,
        'use_slots': bool(layout_rows),
    })


def download_all_photos(request, slug):
    gallery = get_object_or_404(Album, slug=slug)
    if not gallery.allow_downloads:
        return HttpResponse('Downloads are disabled for this gallery.', status=403)

    if gallery.is_showcase:
        photos = [
            item.photo
            for item in gallery.showcase_items.select_related('photo').order_by('order', 'id')
            if item.photo_id
        ]
    else:
        photos = list(gallery.photos.all())

    if not photos:
        return HttpResponse('This gallery has no photos yet.', status=404)

    archive = io.BytesIO()
    used_names = set()

    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for photo in photos:
            if not photo.image:
                continue
            try:
                source_path = photo.image.path
                if not os.path.exists(source_path):
                    continue
                original_name = os.path.basename(source_path)
                name, ext = os.path.splitext(original_name)
                zip_name = original_name
                counter = 2
                while zip_name in used_names:
                    zip_name = f'{name}-{counter}{ext}'
                    counter += 1
                used_names.add(zip_name)
                zf.write(source_path, arcname=zip_name)
            except (ValueError, OSError):
                continue

    archive.seek(0)
    safe_name = gallery.slug or 'gallery'
    response = HttpResponse(archive.read(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{safe_name}-photos.zip"'
    return response
