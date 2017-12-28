# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('dw', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attendance',
            name='date',
            field=models.DateField(default=datetime.date(2017, 12, 25), verbose_name=b'\xe6\x97\xa5\xe6\x9c\x9f'),
        ),
        migrations.AlterField(
            model_name='company_name',
            name='time',
            field=models.DateTimeField(default=datetime.datetime(2017, 12, 25, 15, 47, 37, 849000), verbose_name=b'\xe6\x9b\xb4\xe6\x96\xb0\xe6\x97\xb6\xe9\x97\xb4'),
        ),
        migrations.AlterField(
            model_name='companydepartment',
            name='create_time',
            field=models.DateTimeField(default=datetime.datetime(2017, 12, 25, 15, 47, 37, 843000)),
        ),
        migrations.AlterField(
            model_name='login_title',
            name='time',
            field=models.DateTimeField(default=datetime.datetime(2017, 12, 25, 15, 47, 37, 851000), verbose_name=b'\xe6\x9b\xb4\xe6\x96\xb0\xe6\x97\xb6\xe9\x97\xb4'),
        ),
        migrations.AlterField(
            model_name='milestone',
            name='complete_time',
            field=models.DateTimeField(default=datetime.datetime(2017, 12, 25, 15, 47, 37, 858000), verbose_name=b'\xe5\xae\x9e\xe9\x99\x85\xe5\xae\x8c\xe6\x88\x90\xe6\x97\xb6\xe9\x97\xb4'),
        ),
        migrations.AlterField(
            model_name='milestone',
            name='due',
            field=models.DateTimeField(default=datetime.datetime(2017, 12, 25, 15, 47, 37, 858000), verbose_name=b'\xe9\xa2\x84\xe6\x9c\x9f\xe5\xae\x8c\xe6\x88\x90\xe6\x97\xb6\xe9\x97\xb4'),
        ),
        migrations.AlterField(
            model_name='project',
            name='complete_time',
            field=models.DateTimeField(default=datetime.datetime(2017, 12, 25, 15, 47, 37, 887000), verbose_name=b'\xe5\xae\x9e\xe9\x99\x85\xe5\xae\x8c\xe6\x88\x90\xe6\x97\xb6\xe9\x97\xb4'),
        ),
        migrations.AlterField(
            model_name='project',
            name='due_time',
            field=models.DateTimeField(default=datetime.datetime(2017, 12, 25, 15, 47, 37, 887000), verbose_name=b'\xe9\xa2\x84\xe8\xae\xa1\xe5\xae\x8c\xe6\x88\x90\xe6\x97\xb6\xe9\x97\xb4'),
        ),
        migrations.AlterField(
            model_name='task_team',
            name='create_time',
            field=models.DateTimeField(default=datetime.datetime(2017, 12, 25, 15, 47, 37, 893000)),
        ),
        migrations.AlterField(
            model_name='tasklist',
            name='end_date',
            field=models.DateTimeField(default=datetime.datetime(2017, 12, 25, 15, 47, 37, 956000), verbose_name=b'\xe7\xbb\x93\xe6\x9d\x9f\xe6\x97\xb6\xe9\x97\xb4'),
        ),
        migrations.AlterField(
            model_name='tasklist',
            name='start_date',
            field=models.DateTimeField(default=datetime.datetime(2017, 12, 25, 15, 47, 37, 956000), verbose_name=b'\xe5\xbc\x80\xe5\xa7\x8b\xe6\x97\xb6\xe9\x97\xb4'),
        ),
        migrations.AlterField(
            model_name='taskorder',
            name='end_date',
            field=models.DateTimeField(default=datetime.datetime(2017, 12, 25, 15, 47, 37, 903000), verbose_name=b'\xe5\xae\x9e\xe9\x99\x85\xe7\xbb\x93\xe6\x9d\x9f\xe6\x97\xb6\xe9\x97\xb4'),
        ),
        migrations.AlterField(
            model_name='taskorder',
            name='predict_end_date',
            field=models.DateTimeField(default=datetime.datetime(2017, 12, 25, 15, 47, 37, 903000), verbose_name=b'\xe9\xa2\x84\xe8\xae\xa1\xe7\xbb\x93\xe6\x9d\x9f\xe6\x97\xb6\xe9\x97\xb4'),
        ),
        migrations.AlterField(
            model_name='taskorder',
            name='predict_start_date',
            field=models.DateTimeField(default=datetime.datetime(2017, 12, 25, 15, 47, 37, 903000), verbose_name=b'\xe9\xa2\x84\xe8\xae\xa1\xe8\xb5\xb7\xe5\xa7\x8b\xe6\x97\xb6\xe9\x97\xb4'),
        ),
        migrations.AlterField(
            model_name='taskorder',
            name='start_date',
            field=models.DateTimeField(default=datetime.datetime(2017, 12, 25, 15, 47, 37, 903000), verbose_name=b'\xe5\xae\x9e\xe9\x99\x85\xe8\xb5\xb7\xe5\xa7\x8b\xe6\x97\xb6\xe9\x97\xb4'),
        ),
        migrations.AlterField(
            model_name='user',
            name='entry_time',
            field=models.DateField(default=datetime.date(2017, 12, 25), verbose_name=b'\xe5\x85\xa5\xe8\x81\x8c\xe6\x97\xb6\xe9\x97\xb4'),
        ),
        migrations.AlterField(
            model_name='user',
            name='last_login',
            field=models.DateTimeField(default=datetime.datetime(2017, 12, 25, 15, 47, 37, 835000), null=True, verbose_name=b'\xe6\x9c\x80\xe5\x90\x8e\xe7\x99\xbb\xe5\xbd\x95\xe6\x97\xb6\xe9\x97\xb4', blank=True),
        ),
        migrations.AlterField(
            model_name='wiki_attachment_file',
            name='time',
            field=models.DateTimeField(default=datetime.datetime(2017, 12, 25, 15, 47, 37, 933000), verbose_name=b'\xe4\xb8\x8a\xe4\xbc\xa0\xe6\x97\xb6\xe9\x97\xb4'),
        ),
        migrations.AlterField(
            model_name='wiki_attachment_image',
            name='time',
            field=models.DateTimeField(default=datetime.datetime(2017, 12, 25, 15, 47, 37, 940000), verbose_name=b'\xe4\xb8\x8a\xe4\xbc\xa0\xe6\x97\xb6\xe9\x97\xb4'),
        ),
        migrations.AlterField(
            model_name='wiki_attachment_video',
            name='time',
            field=models.DateTimeField(default=datetime.datetime(2017, 12, 25, 15, 47, 37, 935000), verbose_name=b'\xe4\xb8\x8a\xe4\xbc\xa0\xe6\x97\xb6\xe9\x97\xb4'),
        ),
    ]
