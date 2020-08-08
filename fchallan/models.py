from django.db import models

from client.models import client
from items.models import items
from bill.models import bill
from payment.models import payment

# Create your models here.
class fchallan(models.Model):
    challan_no = models.IntegerField(primary_key=True)
    date = models.DateTimeField()
    client_name = models.ForeignKey(client, on_delete=models.PROTECT)
    gross_amount = models.DecimalField(max_digits = 10,decimal_places = 3)
    gst = models.DecimalField(max_digits = 10,decimal_places = 3)
    other_amount = models.DecimalField(max_digits = 10,decimal_places = 3)
    total_amount = models.DecimalField(max_digits = 10,decimal_places = 3)
    bill_no = models.ForeignKey(bill,null=True, on_delete=models.PROTECT)
    single_bill = models.BooleanField(default = False)
    recieved = models.DecimalField(max_digits = 10,decimal_places = 3)
    payment_no = models.ForeignKey(payment,null=True, on_delete=models.PROTECT)
    deleted = models.BooleanField()

class fjob(models.Model):
    job_id = models.DecimalField(max_digits = 3, decimal_places = 0)
    challan_no = models.ForeignKey(fchallan, on_delete=models.PROTECT)
    job_date = models.DateTimeField()
    job_name = models.CharField(max_length = 120)
    item  = models.ForeignKey(items, on_delete=models.PROTECT)
    quantity = models.BigIntegerField()
    width = models.DecimalField(max_digits = 10,decimal_places = 3)
    height = models.DecimalField(max_digits = 10,decimal_places = 3)
    unit = models.CharField(max_length = 120)
    rate = models.DecimalField(max_digits = 10, decimal_places = 3)
    gst = models.DecimalField(max_digits = 10, decimal_places = 3)
    amount = models.DecimalField(max_digits = 10, decimal_places = 3)