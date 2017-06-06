# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-06 20:30
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('image_compare', '0007_imagemetadata_vectors'),
    ]

    operations = [
        migrations.AddField(
            model_name='imagemetadata',
            name='height',
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='imagemetadata',
            name='width',
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
    ]