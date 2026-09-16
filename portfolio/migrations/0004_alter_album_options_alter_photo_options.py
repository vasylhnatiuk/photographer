from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('portfolio', '0003_gallery_manager'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='album',
            options={'ordering': ['-created_at']},
        ),
        migrations.AlterModelOptions(
            name='photo',
            options={'ordering': ['order', 'id']},
        ),
    ]
