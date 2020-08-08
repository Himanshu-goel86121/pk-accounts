from django.shortcuts import render,get_object_or_404
# Create your views here.
from django.contrib.auth.decorators import login_required
from .models import items
from items_group.models import item_group
from django.contrib.auth.models import User as user
from users.models import Employee

@login_required
def items_add(request):
    items_group = list(item_group.objects.all())
    return render(request,"items_add.html",{"item_groups": items_group})

@login_required
def items_delete(request):
    itemss = list(items.objects.all())
    return render(request,"items_delete.html",{"itemss" : itemss})

@login_required
def items_modify(request):
    itemss = list(items.objects.all())
    return render(request,"items_modify.html",{"itemss" : itemss})

@login_required
def items_get(request):
    items_group = list(item_group.objects.all())
    itemss = list(items.objects.all())
    item_grp = get_object_or_404(items, pk=request.POST['item_name'])
    return render(request,"items_modify.html",{"item_groups":items_group,"itemss" : itemss , "item_grp" : item_grp})

@login_required
def display_items(request):
    itemss = list(items.objects.all())
    return render(request,"items_get.html",{"itemss" : itemss})

@login_required
def add_items(request):
    try:
        items_group = list(item_group.objects.all())
        grp_name = get_object_or_404(item_group, pk=request.POST['group_name'])
        ig = items(item_name = request.POST['item_name'].strip(), group_name = grp_name, unit = request.POST['unit'].strip())
        ig.save()
        return render(request, 'items_add.html', {"item_groups": items_group,
            'success_message': "Item Group saved successfully",
        })
    except Exception as e:
        print(e)
        print(e.__class__.__name__)
        if(str(e.__class__.__name__) == 'DataError'):
            return render(request, 'items_add.html', {"item_groups": items_group,'error_message': "Please provide the data correctly",})
        if(str(e.__class__.__name__) == 'ValidationError'):
            return render(request, 'items_add.html', {"item_groups": items_group,'error_message': "Please provide the data correctly",})
        else:
            return render(request, 'items_add.html', {"item_groups": items_group,'error_message': "Some error occured",})

@login_required
def modify_items(request):
    itemss = list(items.objects.all())
    items_group = list(item_group.objects.all())
    check_user = Employee.objects.get(user = user.objects.get(username = request.user))
    if(check_user.role !='Admin'):
        return render(request, 'items_modify.html', {"itemss" : itemss,'error_message': "You dont have the permission to modify anything",})
    try:
        try:
            items.objects.get(pk=request.POST['item_name'])
        except (KeyError, items.DoesNotExist):
            return render(request, 'items_modify.html', {"item_groups": items_group,"itemss" : itemss,'error_message': "The item group name provided has not been added",})
        grp_name = get_object_or_404(item_group, pk=request.POST['group_name'])
        ig = items(item_name = request.POST['item_name'].strip(), group_name = grp_name, unit = request.POST['unit'].strip())
        ig.save()
        return render(request, 'items_modify.html', {"itemss" : itemss,'success_message': "Item Group saved successfully",})
    except Exception as e:
        print(e)
        print(e.__class__.__name__)
        if(str(e.__class__.__name__) == 'DataError'):
            return render(request, 'items_modify.html', {"item_groups": items_group,"itemss" : itemss,'error_message': "Please provide the data correctly",})
        if(str(e.__class__.__name__) == 'ValidationError'):
            return render(request, 'items_modify.html', {"item_groups": items_group,"itemss" : itemss,'error_message': "Please provide the data correctly",})
        else:
            return render(request, 'items_modify.html', {"item_groups": items_group,"itemss" : itemss,'error_message': "Some error occured",})
        
@login_required
def delete_items(request):
    itemss = list(items.objects.all())
    check_user = Employee.objects.get(user = user.objects.get(username = request.user))
    if(check_user.role !='Admin'):
        return render(request, 'items_delete.html', {"itemss" : itemss,'error_message': "You dont have the permission to modify anything",})
    try:
        try:
            print(itemss)
            selected_choice = items.objects.get(pk='yhiuh')
        except (KeyError, items.DoesNotExist):
            return render(request, 'items_delete.html', {"itemss" : itemss,'error_message': "The item group name provided has not been added",})
        selected_choice.delete()
        itemss = list(items.objects.all())
        return render(request, 'items_delete.html', {"itemss" : itemss,'success_message': "Item Group deleted successfully",})
    except Exception as e:
        print(e)
        print(e.__class__.__name__)
        if(str(e.__class__.__name__) == 'DataError'):
            return render(request, 'items_delete.html', {"itemss" : itemss,'error_message': "Please provide the data correctly",})
        if(str(e.__class__.__name__) == 'ValidationError'):
            return render(request, 'items_delete.html', {"itemss" : itemss,'error_message': "Please provide the data correctly",})
        else:
            return render(request, 'items_delete.html', {"itemss" : itemss,'error_message': "Some error occured",})
    
    