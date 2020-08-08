# -*- coding: utf-8 -*-

from django.urls import path
from . import views

app_name = 'pchallan_app'
urlpatterns = [
    path(r'add/', views.pchallan_add, name='add_page'),
    path(r'add_pchallan/', views.add_pchallan, name='add_pchallan'),
    path(r'add_bill/', views.add_bill, name='add_bill'),
    path(r'filter_date/', views.filter_date, name='filter_date'),
    path(r'filter_client/', views.filter_client, name='filter_client'),
    path(r'filter_challan_no/', views.filter_challan_no, name='filter_challan_no'),
    path(r'delete/', views.pchallan_delete, name='delete_page'),
    path(r'get_pchallan/', views.pchallan_get, name='get_pchallan'),
    path(r'get_pchallan_bill/', views.pchallan_get_bill, name='get_pchallan_bill'),
    path(r'display/', views.pchallan_display, name='display_page'),
    path(r'delete_pchallan/', views.delete_pchallan, name='delete_pchallan'),
    path(r'modify/', views.pchallan_modify, name='modify_page'),
    path(r'modify_bill/', views.pchallan_modify_bill, name='modify_bill_page'),
    path(r'modify_pchallan/', views.modify_pchallan, name='modify_pchallan'),
    path(r'bill_modify_pchallan/', views.bill_modify_pchallan, name='bill_modify_pchallan'),
]