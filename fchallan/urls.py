# -*- coding: utf-8 -*-

from django.urls import path
from . import views

app_name = 'fchallan_app'
urlpatterns = [
    path(r'add/', views.fchallan_add, name='add_page'),
    path(r'add_fchallan/', views.add_fchallan, name='add_fchallan'),
    path(r'add_bill/', views.add_bill, name='add_bill'),
    path(r'filter_date/', views.filter_date, name='filter_date'),
    path(r'display/', views.fchallan_display, name='display_page'),
    path(r'filter_client/', views.filter_client, name='filter_client'),
    path(r'filter_challan_no/', views.filter_challan_no, name='filter_challan_no'),
    path(r'delete/', views.fchallan_delete, name='delete_page'),
    path(r'get_fchallan/', views.fchallan_get, name='get_fchallan'),
    path(r'get_fchallan_bill/', views.fchallan_get_bill, name='get_fchallan_bill'),
    path(r'modify_bill/', views.fchallan_modify_bill, name='modify_bill_page'),
    path(r'bill_modify_fchallan/', views.bill_modify_fchallan, name='bill_modify_fchallan'),
    path(r'delete_fchallan/', views.delete_fchallan, name='delete_fchallan'),
    path(r'modify/', views.fchallan_modify, name='modify_page'),
    path(r'modify_fchallan/', views.modify_fchallan, name='modify_fchallan'),
]