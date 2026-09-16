from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('portfolio', '0002_client_phone_client_preferred_date_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='photo',
            name='album',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='photos',
                to='portfolio.album',
            ),
        ),
        migrations.AddField(
            model_name='album',
            name='client_name',
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name='album',
            name='slug',
            field=models.SlugField(blank=True, max_length=220, unique=True),
        ),
        migrations.AddField(
            model_name='photo',
            name='order',
            field=models.PositiveIntegerField(db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='album',
            name='cover',
            field=models.ImageField(blank=True, null=True, upload_to='gallery_covers/'),
        ),
        migrations.AlterField(
            model_name='photo',
            name='image',
            field=models.ImageField(upload_to='gallery_photos/'),
        ),
    ]
