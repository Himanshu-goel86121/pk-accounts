# -*- coding: utf-8 -*-
from django.urls import path
from . import views

app_name = 'bill_app'
urlpatterns = [
    path(r'get_challans/', views.get_challans, name='get_challans'),
    path(r'add_bill/', views.bill_add, name='add_page'),
    path(r'print_bill/', views.bill_print, name='print_page'),
    path(r'get_jobs/', views.get_jobs, name='get_jobs'),
    path(r'bill_add/', views.add_bill, name='bill_add'),
    path(r'bill_print/', views.print_bill, name='print_bill'),
    path(r'delete/', views.bill_delete, name='delete_page'),
    path(r'delete_bill/', views.delete_bill, name='delete_bill'),
	path(r'filter_date/', views.filter_date, name='filter_date'),
    path(r'filter_client/', views.filter_client, name='filter_client'),
	path(r'display/', views.bill_display, name='display_page'),
]