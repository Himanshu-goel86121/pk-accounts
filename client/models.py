from django.db import models

# Create your models here.

import json

class client(models.Model):
    client_name = models.CharField(max_length = 80,primary_key = True)
    under_bank_accounts = models.CharField(max_length = 40)
    balance = models.DecimalField(max_digits = 10,decimal_places = 3)
    address = models.CharField(max_length = 120)
    city = models.CharField(max_length = 40)
    state = models.CharField(max_length = 40)
    pincode = models.CharField(max_length = 6)
    phone1 = models.CharField(max_length = 10)
    phone2 = models.CharField(max_length = 10)
    gstin = models.CharField(max_length = 15)
    pan_no = models.CharField(max_length = 10)
    email = models.CharField(max_length = 100)
    nickname = models.CharField(max_length = 100)
    
    
    def __str__(self):
        return json.dumps({"client_name" : self.client_name ,"email" : self.email ,"gstin" : self.gstin , "pan_no" : self.pan_no,"phone1" : self.phone1 , "phone2" : self.phone2,"state" : self.state , "pincode" : self.pincode,"address" : self.address , "city" : self.city, "under_bank_accounts" : self.under_bank_accounts, "balance" : str(self.balance)})