from django.db import models

# Create your models here.

class logs(models.Model):
    user_name = models.CharField(max_length = 80)
    message  = models.CharField(max_length = 4000)
    date = models.DateTimeField(auto_now_add=True)