from io import BytesIO
import os
import uuid

from django.core.files.base import ContentFile
from django.db import IntegrityError, models
from django.utils.text import slugify
from PIL import Image, ImageOps


def optimize_image(uploaded_file, max_size=2048, quality=85):
    """Resize and compress an uploaded image for web delivery."""
    uploaded_file.seek(0)
    image = Image.open(uploaded_file)
    image = ImageOps.exif_transpose(image)

    if image.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', image.size, 'white')
        if image.mode == 'P':
            image = image.convert('RGBA')
        background.paste(image, mask=image.getchannel('A') if 'A' in image.getbands() else None)
        image = background
    else:
        image = image.convert('RGB')

    image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

    output = BytesIO()
    image.save(output, format='JPEG', quality=quality, optimize=True, progressive=True)
    output.seek(0)

    original_name = os.path.basename(getattr(uploaded_file, 'name', 'image.jpg'))
    base_name = os.path.splitext(original_name)[0] or 'image'
    return ContentFile(output.read(), name=f'{base_name}.jpg')


class Album(models.Model):
    CLIENT = 'client'
    SHOWCASE = 'showcase'
    GALLERY_TYPES = [
        (CLIENT, 'Client gallery'),
        (SHOWCASE, 'General / portfolio gallery'),
    ]

    WEDDINGS = 'weddings'
    PROPOSALS = 'proposals'
    LOVE_STORIES = 'love_stories'
    OTHER = 'other'
    SHOWCASE_CATEGORIES = [
        (WEDDINGS, 'Weddings'),
        (PROPOSALS, 'Proposals'),
        (LOVE_STORIES, 'Love Stories'),
        (OTHER, 'Other'),
    ]

    title = models.CharField(max_length=200)
    client_name = models.CharField(max_length=150, blank=True)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(blank=True)
    lightroom_url = models.URLField(blank=True)

    gallery_type = models.CharField(
        max_length=20,
        choices=GALLERY_TYPES,
        default=CLIENT,
        db_index=True,
    )
    showcase_category = models.CharField(
        max_length=30,
        choices=SHOWCASE_CATEGORIES,
        default=LOVE_STORIES,
        blank=True,
    )
    display_order = models.PositiveIntegerField(default=0, db_index=True)

    # Visibility / client permissions
    is_private = models.BooleanField(default=True)
    allow_downloads = models.BooleanField(default=True)

    # Main cover used on the client gallery hero.
    cover = models.ImageField(upload_to='gallery_covers/', blank=True, null=True)

    # Optional alternative cover for the public Love Stories / portfolio page.
    love_stories_cover = models.ImageField(
        upload_to='love_stories_covers/', blank=True, null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['display_order', '-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title) or 'gallery'
            slug = base
            counter = 2
            while Album.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{counter}'
                counter += 1
            self.slug = slug

        # Keep showcase category meaningful only for showcase galleries.
        if self.gallery_type == self.CLIENT:
            self.showcase_category = self.LOVE_STORIES

        if self.cover and getattr(self.cover, '_needs_optimization', False):
            optimized = optimize_image(self.cover.file)
            self.cover.save(optimized.name, optimized, save=False)

        if self.love_stories_cover and getattr(self.love_stories_cover, '_needs_optimization', False):
            optimized = optimize_image(self.love_stories_cover.file)
            self.love_stories_cover.save(optimized.name, optimized, save=False)

        try:
            super().save(*args, **kwargs)
        except IntegrityError as exc:
            if self.slug and 'portfolio_album.slug' in str(exc):
                base = slugify(self.title) or 'gallery'
                self.slug = f'{base}-{uuid.uuid4().hex[:8]}'
                super().save(*args, **kwargs)
            else:
                raise

    @property
    def is_showcase(self):
        return self.gallery_type == self.SHOWCASE

    @property
    def is_client_gallery(self):
        return self.gallery_type == self.CLIENT

    def __str__(self):
        return self.title


class Photo(models.Model):
    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name='photos')
    title = models.CharField(max_length=200, blank=True)
    image = models.ImageField(upload_to='gallery_photos/')
    description = models.TextField(blank=True)
    is_featured = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'id']

    def save(self, *args, **kwargs):
        if self.image and getattr(self.image, '_needs_optimization', False):
            optimized = optimize_image(self.image.file)
            self.image.save(optimized.name, optimized, save=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title or self.image.name


class ShowcasePhoto(models.Model):
    """A photo selected from a client gallery for a general portfolio gallery."""
    album = models.ForeignKey(
        Album,
        on_delete=models.CASCADE,
        related_name='showcase_items',
        limit_choices_to={'gallery_type': Album.SHOWCASE},
    )
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE, related_name='showcase_items')
    order = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        ordering = ['order', 'id']
        constraints = [
            models.UniqueConstraint(
                fields=['album', 'photo'],
                name='unique_showcase_photo',
            )
        ]

    def __str__(self):
        return f'{self.album.title} → {self.photo}'


class Client(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(null=True, blank=True)
    preferred_date = models.DateField(null=True, blank=True)
    preferred_time = models.TimeField(null=True, blank=True)
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
