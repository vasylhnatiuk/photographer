from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('portfolio', '0005_album_gallery_settings'),
    ]

    operations = [
        migrations.AddField(
            model_name='album',
            name='display_order',
            field=models.PositiveIntegerField(db_index=True, default=0),
        ),
        migrations.AddField(
            model_name='album',
            name='gallery_type',
            field=models.CharField(
                choices=[
                    ('client', 'Client gallery'),
                    ('showcase', 'General / portfolio gallery'),
                ],
                db_index=True,
                default='client',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='album',
            name='showcase_category',
            field=models.CharField(
                blank=True,
                choices=[
                    ('weddings', 'Weddings'),
                    ('proposals', 'Proposals'),
                    ('love_stories', 'Love Stories'),
                    ('other', 'Other'),
                ],
                default='love_stories',
                max_length=30,
            ),
        ),
        migrations.CreateModel(
            name='ShowcasePhoto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.PositiveIntegerField(db_index=True, default=0)),
                ('album', models.ForeignKey(
                    limit_choices_to={'gallery_type': 'showcase'},
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='showcase_items',
                    to='portfolio.album',
                )),
                ('photo', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='showcase_items',
                    to='portfolio.photo',
                )),
            ],
            options={
                'ordering': ['order', 'id'],
            },
        ),
        migrations.AddConstraint(
            model_name='showcasephoto',
            constraint=models.UniqueConstraint(
                fields=('album', 'photo'),
                name='unique_showcase_photo',
            ),
        ),
    ]
