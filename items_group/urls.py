from django.urls import path
from . import views

app_name = 'items_group_app'
urlpatterns = [
    path(r'add/', views.items_group_add, name='add_page'),
    path(r'add_items_group/', views.add_items_group, name='add_items_group'),
    path(r'modify/', views.items_group_modify, name='modify_page'),
    path(r'delete/', views.items_group_delete, name='delete_page'),
    path(r'get_item_group/', views.items_group_get, name='get_item_group'),
    path(r'display/', views.items_group_display, name='display_page'),
    path(r'delete_item_group/', views.delete_items_group, name='delete_item_group'),
    path(r'modify_items_group/', views.modify_items_group, name='modify_items_group'),
]