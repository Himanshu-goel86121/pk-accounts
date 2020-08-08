# -*- coding: utf-8 -*-
from django.urls import path
from . import views

app_name = 'client_app'
urlpatterns = [
    path(r'add/', views.client_add, name='add_page'),
    path(r'add_client/', views.add_client, name='add_client'),
    path(r'modify/', views.client_modify, name='modify_page'),
    path(r'delete/', views.client_delete, name='delete_page'),
    path(r'display/', views.client_display, name='display_page'),
    path(r'get_client/', views.client_get, name='get_client'),
    path(r'delete_client/', views.delete_client, name='delete_client'),
    path(r'modify_client/', views.modify_client, name='modify_client'),
]
