# Generated by Django 2.0 on 2018-01-27 10:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pchallan', '0005_auto_20180125_0558'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pchallan',
            name='billed',
        ),
        migrations.AddField(
            model_name='pchallan',
            name='recieved',
            field=models.DecimalField(decimal_places=3, default=0, max_digits=10),
            preserve_default=False,
        ),
    ]