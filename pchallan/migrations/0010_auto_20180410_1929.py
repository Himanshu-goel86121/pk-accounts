# Generated by Django 2.0 on 2018-04-10 13:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pchallan', '0009_auto_20180131_0018'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pchallan',
            name='challan_no',
            field=models.IntegerField(primary_key=True, serialize=False),
        ),
    ]
