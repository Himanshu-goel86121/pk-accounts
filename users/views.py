from django.shortcuts import render
from django.db import transaction
# Create your views here.
from django.shortcuts import render,get_object_or_404
# Create your views here.
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User as user
from .models import Employee
@login_required
def user_add(request):
    return render(request,"user_add.html")

@login_required
def user_delete(request):
    users = list(user.objects.all())
    return render(request,"user_delete.html",{"users" : users})

@login_required    
def user_get(request):
    users = list(user.objects.all())
    user_grp = get_object_or_404(user, username=request.POST['username'])
    return render(request,"user_modify.html",{"users" : users , "user_grp" : user_grp})

@login_required
def add_user(request):
    try:
        user_add = user(username = request.POST['username'].strip(), email = request.POST['email'].strip())
        user_add.set_password(request.POST['password'])
        user_add.save()
        emp = Employee(user = user_add, role = request.POST['role'].strip())
        emp.save()
        return render(request, 'user_add.html', {
            'success_message': "user Group saved successfully",
        })
    except Exception as e:
        print(e)
        print(e.__class__.__name__)
        if(str(e.__class__.__name__) == 'DataError'):
            return render(request, 'user_add.html', {'error_message': "Please provide the data correctly",})
        if(str(e.__class__.__name__) == 'ValidationError'):
            return render(request, 'user_add.html', {'error_message': "Please provide the data correctly",})
        else:
            return render(request, 'user_add.html', {'error_message': "Some error occured",})

@login_required
def delete_user(request):
    users = list(user.objects.all())
    check_user = Employee.objects.get(user = user.objects.get(username = request.user))
    if(check_user.role !='Admin'):
        return render(request, 'user_delete.html', {"users" : users,'error_message': "You dont have the permission to modify anything",})
    try:
        try:
            selected_choice = user.objects.get(username=request.POST['username'])
        except (KeyError, user.DoesNotExist):
            return render(request, 'user_delete.html', {"users" : users,'error_message': "The user group name provided has not been added",})
        selected_choice.delete()
        users = list(user.objects.all())
        return render(request, 'user_delete.html', {"users" : users,'success_message': "user Group deleted successfully",})
    except Exception as e:
        print(e)
        print(e.__class__.__name__)
        if(str(e.__class__.__name__) == 'DataError'):
            return render(request, 'user_delete.html', {"users" : users,'error_message': "Please provide the data correctly",})
        if(str(e.__class__.__name__) == 'ValidationError'):
            return render(request, 'user_delete.html', {"users" : users,'error_message': "Please provide the data correctly",})
        else:
            return render(request, 'user_delete.html', {"users" : users,'error_message': "Some error occured",})
    
    