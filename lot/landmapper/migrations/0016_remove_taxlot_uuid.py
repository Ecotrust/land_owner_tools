# Generated by Django 2.2.12 on 2020-11-16 09:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('landmapper', '0015_auto_20201103_1445'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='taxlot',
            name='uuid',
        ),
    ]