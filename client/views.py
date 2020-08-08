from django.shortcuts import render,get_object_or_404
# Create your views here.
from django.contrib.auth.decorators import login_required
from .models import client
from django.contrib.auth.models import User as user
from users.models import Employee
@login_required
def client_add(request):
    return render(request,"client_add.html")

@login_required
def client_delete(request):
    clients = list(client.objects.all().order_by('client_name'))
    return render(request,"client_delete.html",{"clients" : clients})

@login_required
def client_modify(request):
    clients = list(client.objects.all().order_by('client_name'))
    print(clients)
    return render(request,"client_modify.html",{"clients" : clients})

@login_required
def client_display(request):
    clients = list(client.objects.all().order_by('client_name'))
    return render(request,"client_get.html",{"clients" : clients})

@login_required
def client_get(request):
    clients = list(client.objects.all().order_by('client_name'))
    item_grp = get_object_or_404(client, pk=request.POST['client_name'])
    print(item_grp)
    return render(request,"client_modify.html",{"clients" : clients , "client_grp" : item_grp})

@login_required
def add_client(request):
    try:
        ig = client(client_name = request.POST['client_name'].strip(), under_bank_accounts = request.POST['under_bank_accounts'], balance = request.POST['balance'],address = request.POST['address'].strip(), city = request.POST['city'].strip(), state = request.POST['state'].strip(),pincode = request.POST['pincode'].strip(), phone1 = request.POST['phone1'].strip(), phone2 = request.POST['phone2'].strip(),gstin = request.POST['gstin'].strip(), pan_no = request.POST['pan_no'].strip(),nickname = request.POST['nickname'].strip(), email = request.POST['email'].strip())
        ig.save()
        return render(request, 'client_add.html', {
            'success_message': "Client saved successfully",
        })
    except Exception as e:
        print(e)
        print(e.__class__.__name__)
        if(str(e.__class__.__name__) == 'DataError'):
            return render(request, 'client_add.html', {'error_message': "Please provide the data correctly",})
        if(str(e.__class__.__name__) == 'ValidationError'):
            return render(request, 'client_add.html', {'error_message': "Please provide the data correctly",})
        else:
            return render(request, 'client_add.html', {'error_message': "Some error occured",})
@login_required
def modify_client(request):
    clients = list(client.objects.all().order_by('client_name'))
    check_user = Employee.objects.get(user = user.objects.get(username = request.user))
    if(check_user.role !='Admin'):
        return render(request, 'client_modify.html', {"clients" : clients,'error_message': "You dont have the permission to modify anything",})
    try:
        try:
            selected_choice = client.objects.get(pk=request.POST['client_name'])
        except (KeyError, client.DoesNotExist):
            return render(request, 'client_modify.html', {"clients" : clients,'error_message': "The item group name provided has not been added",})
        selected_choice.client_name = request.POST['client_name'].strip()
        print(selected_choice.client_name)
        print(request.POST['nickname'].strip())
        selected_choice.under_bank_accounts = request.POST['under_bank_accounts']
        selected_choice.balance = request.POST['balance']
        selected_choice.address = request.POST['address'].strip()
        selected_choice.city = request.POST['city'].strip()
        selected_choice.state = request.POST['state'].strip()
        selected_choice.pincode = request.POST['pincode'].strip()
        selected_choice.phone1 = request.POST['phone1'].strip()
        selected_choice.phone2 = request.POST['phone2'].strip()
        selected_choice.gstin = request.POST['gstin'].strip()
        selected_choice.pan_no = request.POST['pan_no'].strip()
        selected_choice.email = request.POST['email'].strip()
        selected_choice.nickname = request.POST['nickname'].strip()
        print(selected_choice.nickname)
        selected_choice.save()
        print(selected_choice.nickname)
        print(selected_choice)
        return render(request, 'client_modify.html', {"clients" : clients,'success_message': "Item Group saved successfully",})
    except Exception as e:
        print(e)
        print(e.__class__.__name__)
        if(str(e.__class__.__name__) == 'DataError'):
            return render(request, 'client_modify.html', {"clients" : clients,'error_message': "Please provide the data correctly",})
        if(str(e.__class__.__name__) == 'ValidationError'):
            return render(request, 'client_modify.html', {"clients" : clients,'error_message': "Please provide the data correctly",})
        else:
            return render(request, 'client_modify.html', {"clients" : clients,'error_message': "Some error occured",})
        
@login_required
def delete_client(request):
    clients = list(client.objects.all().order_by('client_name'))
    check_user = Employee.objects.get(user = user.objects.get(username = request.user))
    if(check_user.role !='Admin'):
        return render(request, 'client_delete.html', {"clients" : clients,'error_message': "You dont have the permission to modify anything",})
    try:
        print('The client name is :[]',request.POST['client_name']+'[]')
        try:
            selected_choice = client.objects.get(pk=request.POST['client_name'])
        except (KeyError, client.DoesNotExist):
            return render(request, 'client_delete.html', {"clients" : clients,'error_message': "The item group name provided has not been added",})
        selected_choice.delete()
        clients = list(client.objects.all())
        return render(request, 'client_delete.html', {"clients" : clients,'success_message': "Item Group deleted successfully",})
    except Exception as e:
        print(e)
        raise
        print(e.__class__.__name__)
        if(str(e.__class__.__name__) == 'DataError'):
            return render(request, 'client_delete.html', {"clients" : clients,'error_message': "Please provide the data correctly",})
        if(str(e.__class__.__name__) == 'ValidationError'):
            return render(request, 'client_delete.html', {"clients" : clients,'error_message': "Please provide the data correctly",})
        else:
            return render(request, 'client_delete.html', {"clients" : clients,'error_message': "Some error occured",})
    