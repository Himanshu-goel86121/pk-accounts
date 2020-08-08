# Generated by Django 2.0 on 2018-01-13 13:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('client', '0001_initial'),
        ('items', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='pchallan',
            fields=[
                ('challan_no', models.AutoField(primary_key=True, serialize=False)),
                ('date', models.DateTimeField()),
                ('job_date', models.DateTimeField()),
                ('gross_amount', models.DecimalField(decimal_places=3, max_digits=10)),
                ('gst', models.DecimalField(decimal_places=3, max_digits=10)),
                ('other_amount', models.DecimalField(decimal_places=3, max_digits=10)),
                ('total_amount', models.DecimalField(decimal_places=3, max_digits=10)),
                ('balance', models.DecimalField(decimal_places=3, max_digits=10)),
                ('billed', models.BooleanField()),
                ('deleted', models.BooleanField()),
                ('slip_no', models.DecimalField(decimal_places=0, max_digits=10)),
                ('client_name', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='client.client')),
            ],
        ),
        migrations.CreateModel(
            name='pjob',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('job_id', models.DecimalField(decimal_places=0, max_digits=3)),
                ('job_name', models.CharField(max_length=120)),
                ('quantity', models.BigIntegerField()),
                ('unit', models.CharField(max_length=120)),
                ('rate', models.DecimalField(decimal_places=3, max_digits=10)),
                ('amount', models.DecimalField(decimal_places=3, max_digits=10)),
                ('challan_no', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='pchallan.pchallan')),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='items.items')),
            ],
        ),
    ]