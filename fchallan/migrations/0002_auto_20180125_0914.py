# Generated by Django 2.0 on 2018-01-25 17:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fchallan', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='fjob',
            name='height',
            field=models.DecimalField(decimal_places=0, default=0, max_digits=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='fjob',
            name='width',
            field=models.DecimalField(decimal_places=0, default=0, max_digits=10),
            preserve_default=False,
        ),
    ]