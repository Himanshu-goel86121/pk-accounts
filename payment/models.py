from django.db import models
from client.models import client


# Create your models here.

class payment(models.Model):
    payment_no = models.AutoField(primary_key=True)
    date = models.DateTimeField()
    client_name = models.ForeignKey(client, on_delete=models.PROTECT)
    is_bill_payment = models.BooleanField()
    remaining_payment = models.DecimalField(max_digits=10, decimal_places=3)
    check_no = models.CharField(max_length=120, null=True)
    check_date = models.DateTimeField(null=True)
    bank_name = models.CharField(max_length=120, null=True)
    pay_type = models.CharField(max_length=10, null=True)
