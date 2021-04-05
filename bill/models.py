from django.db import models
from client.models import client
from payment.models import payment


# Create your models here.
class bill(models.Model):
    bill_no = models.IntegerField(primary_key=True)
    date = models.DateTimeField()
    client_name = models.ForeignKey(client, on_delete=models.PROTECT)
    gross_amount = models.DecimalField(max_digits=10, decimal_places=3)
    gst = models.DecimalField(max_digits=10, decimal_places=3)
    other_amount = models.DecimalField(max_digits=10, decimal_places=3)
    total_amount = models.DecimalField(max_digits=10, decimal_places=3)
    recieved = models.DecimalField(max_digits=10, decimal_places=3)
    payment_no = models.ForeignKey(payment, null=True, on_delete=models.PROTECT)
    deleted = models.BooleanField()
