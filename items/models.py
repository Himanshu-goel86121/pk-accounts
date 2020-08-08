from django.db import models
from items_group.models import item_group
# Create your models here.

class items(models.Model):
    item_name = models.CharField(max_length = 60,primary_key = True)
    group_name = models.ForeignKey(item_group, on_delete=models.PROTECT)
    unit = models.CharField(max_length = 25)