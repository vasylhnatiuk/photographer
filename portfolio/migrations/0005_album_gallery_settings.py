from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('portfolio', '0004_album_lightroom_url'),
        ('portfolio', '0004_alter_album_options_alter_photo_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='album',
            name='allow_downloads',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='album',
            name='is_private',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='album',
            name='love_stories_cover',
            field=models.ImageField(blank=True, null=True, upload_to='love_stories_covers/'),
        ),
    ]
