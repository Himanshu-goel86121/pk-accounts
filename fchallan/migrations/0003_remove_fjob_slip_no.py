# Generated by Django 2.0 on 2018-01-25 19:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('fchallan', '0002_auto_20180125_0914'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='fjob',
            name='slip_no',
        ),
    ]
