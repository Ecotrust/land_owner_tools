# Generated by Django 2.2.12 on 2020-08-10 17:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('landmapper', '0006_property_property_map_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='property',
            name='scalebar_image',
            field=models.ImageField(null=True, upload_to=None),
        ),
    ]
