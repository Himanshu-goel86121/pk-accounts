# -*- coding: utf-8 -*-
from django.urls import path
from . import views

app_name = 'payment_app'
urlpatterns = [
    path(r'add/', views.payment_add, name='add_page'),
    path(r'get_challans/', views.get_challans, name='get_challans'),
    path(r'add_payment/', views.add_payment, name='add_payment'),
    path(r'delete/', views.payment_delete, name='delete_page'),
    path(r'delete_payment/', views.delete_payment, name='delete_payment'),
    path(r'add_bill/', views.payment_add_bill, name='add_page_bill'),
    path(r'get_challans_bill/', views.get_challans_bill, name='get_challans_bill'),
    path(r'add_payment_bill/', views.add_payment_bill, name='add_payment_bill'),
    path(r'payment_print/', views.payment_print, name='payment_print'),
    path(r'print_payment/', views.print_payment, name='print_payment'),
    path(r'filter_date/', views.filter_date, name='filter_date'),
    path(r'filter_client/', views.filter_client, name='filter_client'),
	path(r'display/', views.payment_display, name='display_page'),
]
