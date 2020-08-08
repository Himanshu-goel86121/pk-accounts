from django.db import models

# Create your models here.

import json

class item_group(models.Model):
    item_group_name = models.CharField(max_length = 80,primary_key = True)
    hsn_code = models.CharField(max_length = 8)
    tax = models.DecimalField(max_digits = 7,decimal_places = 4)
    def __str__(self):
        return json.dumps({"item_group_name" : self.item_group_name , "hsn_code" : self.hsn_code, "tax" : str(self.tax)})