# Generated by Django 2.0 on 2018-01-27 15:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('fchallan', '0004_auto_20180127_0423'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='fchallan',
            name='recieved',
        ),
        migrations.AlterField(
            model_name='fjob',
            name='challan_no',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='fchallan.fchallan'),
        ),
    ]
