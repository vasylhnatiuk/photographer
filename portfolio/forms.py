from django import forms
from .models import Album


class GalleryForm(forms.ModelForm):
    class Meta:
        model = Album
        fields = [
            'title',
            'client_name',
            'description',
            'gallery_type',
            'showcase_category',
            'lightroom_url',
            'cover',
            'love_stories_cover',
            'is_private',
            'allow_downloads',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'e.g. Sarah & James — Central Park'}),
            'client_name': forms.TextInput(attrs={'placeholder': 'Client name'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Optional note for the gallery'}),
            'gallery_type': forms.Select(),
            'showcase_category': forms.Select(),
            'lightroom_url': forms.URLInput(attrs={'placeholder': 'https://lightroom.adobe.com/...'}),
            'is_private': forms.CheckboxInput(),
            'allow_downloads': forms.CheckboxInput(),
        }


class MultipleFileInput(forms.FileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        if not data:
            return []
        single_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_clean(item, initial) for item in data]
        return [single_clean(data, initial)]


class PhotoUploadForm(forms.Form):
    photos = MultipleFileField(
        required=False,
        widget=MultipleFileInput(attrs={
            'accept': 'image/jpeg,image/png,image/webp',
            'multiple': True,
        }),
    )
