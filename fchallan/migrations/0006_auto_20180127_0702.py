# Generated by Django 2.0 on 2018-01-27 15:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bill', '0001_initial'),
        ('fchallan', '0005_auto_20180127_0700'),
    ]

    operations = [
        migrations.AddField(
            model_name='fchallan',
            name='bill_no',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='bill.bill'),
        ),
        migrations.AlterField(
            model_name='fjob',
            name='challan_no',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='fchallan.fchallan'),
        ),
    ]