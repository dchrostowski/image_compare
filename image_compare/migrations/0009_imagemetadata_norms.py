# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-06 21:31
from __future__ import unicode_literals

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('image_compare', '0008_auto_20170606_2030'),
    ]

    operations = [
        migrations.AddField(
            model_name='imagemetadata',
            name='norms',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.DecimalField(decimal_places=4, max_digits=10), default=[0.0], size=None),
        ),
    ]