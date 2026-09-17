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
            'access_password',
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
            'access_password': forms.TextInput(attrs={'placeholder': '1212'}),
            'allow_downloads': forms.CheckboxInput(),
        }


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class PhotoUploadForm(forms.Form):
    photos = forms.FileField(
        required=False,
        widget=MultipleFileInput(attrs={
            'accept': 'image/jpeg,image/png,image/webp,image/jpg',
            'multiple': True,
        }),
    )
