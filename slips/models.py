from django.db import models

from client.models import client
from items.models import items

# Create your models here.
class slip(models.Model):
    slip_no = models.AutoField(primary_key=True)
    date = models.DateTimeField()
    client_name = models.ForeignKey(client, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits = 10,decimal_places = 3)
    completed = models.BooleanField()
    billed = models.BooleanField()


class slip_job(models.Model):
    job_id = models.DecimalField(max_digits = 3, decimal_places = 0)
    slip_no = models.ForeignKey(slip, on_delete=models.PROTECT)
    job_name = models.CharField(max_length = 120)
    item  = models.ForeignKey(items, on_delete=models.PROTECT)
    quantity = models.BigIntegerField()
    rate = models.DecimalField(max_digits = 10, decimal_places = 3)
    amount = models.DecimalField(max_digits = 10, decimal_places = 3)
    fb = models.BooleanField()
    completed = models.BooleanField()
