from django.shortcuts import render,get_object_or_404
# Create your views here.
from django.contrib.auth.decorators import login_required
from .models import item_group
from django.contrib.auth.models import User as user
from users.models import Employee
@login_required
def items_group_add(request):
    return render(request,"items_group_add.html")

@login_required
def items_group_delete(request):
    items_groups = list(item_group.objects.all())
    return render(request,"items_group_delete.html",{"item_groups" : items_groups})

@login_required
def items_group_display(request):
    items_groups = list(item_group.objects.all())
    return render(request,"items_group_get.html",{"item_groups" : items_groups})

@login_required
def items_group_modify(request):
    items_groups = list(item_group.objects.all())
    return render(request,"items_group_modify.html",{"item_groups" : items_groups})

@login_required
def items_group_get(request):
    items_groups = list(item_group.objects.all())
    item_grp = get_object_or_404(item_group, pk=request.POST['item_group_name'])
    return render(request,"items_group_modify.html",{"item_groups" : items_groups , "item_grp" : item_grp})

@login_required
def add_items_group(request):
    try:
        ig = item_group(item_group_name = request.POST['item_group_name'].strip(), hsn_code = request.POST['hsn_code'].strip(), tax = request.POST['tax'])
        ig.save()
        return render(request, 'items_group_add.html', {
            'success_message': "Item Group saved successfully",
        })
    except Exception as e:
        print(e)
        print(e.__class__.__name__)
        if(str(e.__class__.__name__) == 'DataError'):
            return render(request, 'items_group_add.html', {'error_message': "Please provide the data correctly",})
        if(str(e.__class__.__name__) == 'ValidationError'):
            return render(request, 'items_group_add.html', {'error_message': "Please provide the data correctly",})
        else:
            return render(request, 'items_group_add.html', {'error_message': "Some error occured",})

@login_required
def modify_items_group(request):
    items_groups = list(item_group.objects.all())
    check_user = Employee.objects.get(user = user.objects.get(username = request.user))
    if(check_user.role !='Admin'):
        return render(request, 'items_group_modify.html', {"items_groups" : items_groups,'error_message': "You dont have the permission to modify anything",})
    try:
        try:
            selected_choice = item_group.objects.get(pk=request.POST['item_group_name'])
        except (KeyError, item_group.DoesNotExist):
            return render(request, 'items_group_modify.html', {"item_groups" : items_groups,'error_message': "The item group name provided has not been added",})
        ig = item_group(item_group_name = request.POST['item_group_name'].strip(), hsn_code = request.POST['hsn_code'].strip(), tax = request.POST['tax'])
        ig.save()
        return render(request, 'items_group_modify.html', {"item_groups" : items_groups,'success_message': "Item Group saved successfully",})
    except Exception as e:
        print(e)
        print(e.__class__.__name__)
        if(str(e.__class__.__name__) == 'DataError'):
            return render(request, 'items_group_modify.html', {"item_groups" : items_groups,'error_message': "Please provide the data correctly",})
        if(str(e.__class__.__name__) == 'ValidationError'):
            return render(request, 'items_group_modify.html', {"item_groups" : items_groups,'error_message': "Please provide the data correctly",})
        else:
            return render(request, 'items_group_modify.html', {"item_groups" : items_groups,'error_message': "Some error occured",})
        
@login_required
def delete_items_group(request):
    items_groups = list(item_group.objects.all())
    check_user = Employee.objects.get(user = user.objects.get(username = request.user))
    if(check_user.role !='Admin'):
        return render(request, 'items_group_delete.html', {"item_groups" : items_groups,'error_message': "You dont have the permission to modify anything",})
    try:
        try:
            selected_choice = item_group.objects.get(pk=request.POST['item_group_name'])
        except (KeyError, item_group.DoesNotExist):
            return render(request, 'items_group_delete.html', {"item_groups" : items_groups,'error_message': "The item group name provided has not been added",})
        selected_choice.delete()
        items_groups = list(item_group.objects.all())
        return render(request, 'items_group_delete.html', {"item_groups" : items_groups,'success_message': "Item Group deleted successfully",})
    except Exception as e:
        print(e)
        print(e.__class__.__name__)
        if(str(e.__class__.__name__) == 'DataError'):
            return render(request, 'items_group_delete.html', {"item_groups" : items_groups,'error_message': "Please provide the data correctly",})
        if(str(e.__class__.__name__) == 'ValidationError'):
            return render(request, 'items_group_delete.html', {"item_groups" : items_groups,'error_message': "Please provide the data correctly",})
        else:
            return render(request, 'items_group_delete.html', {"item_groups" : items_groups,'error_message': "Some error occured",})
    
    