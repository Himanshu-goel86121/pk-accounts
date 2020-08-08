# Generated by Django 2.0 on 2018-01-06 16:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('items_group', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='items',
            fields=[
                ('item_name', models.CharField(max_length=60, primary_key=True, serialize=False)),
                ('unit', models.CharField(max_length=25)),
                ('group_name', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='items_group.item_group')),
            ],
        ),
    ]
