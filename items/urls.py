# -*- coding: utf-8 -*-

from django.urls import path
from . import views

app_name = 'items_app'
urlpatterns = [
    path(r'add/', views.items_add, name='add_page'),
    path(r'add_items/', views.add_items, name='add_items'),
    path(r'delete/', views.items_delete, name='delete_page'),
    path(r'get_items/', views.items_get, name='get_items'),
    path(r'display/', views.display_items, name='display_page'),
    path(r'delete_items/', views.delete_items, name='delete_items'),
    path(r'modify/', views.items_modify, name='modify_page'),
    path(r'modify_items/', views.modify_items, name='modify_items'),
]