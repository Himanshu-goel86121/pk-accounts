from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from logs.models import logs
# Create your views here.
# this login required decorator is to not allow to any  
# view without authenticating
@login_required(login_url="login/")
def home(request):
    messages = logs.objects.all().order_by("date")[::-1][:1000]
    return render(request,"home.html",{"messages":messages})