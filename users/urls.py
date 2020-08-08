# -*- coding: utf-8 -*-

from django.urls import path
from . import views

app_name = 'user_app'
print("url called")
urlpatterns = [
    path(r'add/', views.user_add, name='add_page'),
    path(r'add_user/', views.add_user, name='add_user'),
    path(r'delete/', views.user_delete, name='delete_page'),
    path(r'get_user/', views.user_get, name='get_user'),
    path(r'delete_user/', views.delete_user, name='delete_user'),
]