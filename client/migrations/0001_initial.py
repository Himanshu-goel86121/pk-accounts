# Generated by Django 2.0 on 2017-12-31 12:50

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='client',
            fields=[
                ('client_name', models.CharField(max_length=80, primary_key=True, serialize=False)),
                ('under_bank_accounts', models.CharField(max_length=40)),
                ('balance', models.DecimalField(decimal_places=3, max_digits=10)),
                ('address', models.CharField(max_length=120)),
                ('city', models.CharField(max_length=40)),
                ('state', models.CharField(max_length=40)),
                ('pincode', models.CharField(max_length=6)),
                ('phone1', models.CharField(max_length=10)),
                ('phone2', models.CharField(max_length=10)),
                ('gstin', models.CharField(max_length=15)),
                ('pan_no', models.CharField(max_length=10)),
                ('email', models.CharField(max_length=100)),
            ],
        ),
    ]