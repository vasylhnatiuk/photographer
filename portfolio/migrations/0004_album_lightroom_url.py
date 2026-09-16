from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('portfolio', '0003_gallery_manager'),
    ]

    operations = [
        migrations.AddField(
            model_name='album',
            name='lightroom_url',
            field=models.URLField(blank=True),
        ),
    ]
