# -*- coding: utf-8 -*-

from django.urls import path
from . import views

app_name = 'report_app'
urlpatterns = [
    path(r'report_page/', views.report_page, name='report_page'),
    path(r'due_list_pchallan_get/', views.due_list_pchallan_get, name='due_list_pchallan_get'),
	path(r'due_list_partywise_pchallan_get/', views.due_list_partywise_pchallan_get, name='due_list_partywise_pchallan_get'),
	path(r'due_list_partywise_bill_get/', views.due_list_partywise_bill_get, name='due_list_partywise_bill_get'),
    path(r'due_list_fchallan_get/', views.due_list_fchallan_get, name='due_list_fchallan_get'),
    path(r'sales_register_get/', views.sales_register_get, name='sales_register_get'),
    path(r'b2b_report_get/', views.b2b_report_get, name='b2b_report_get'),
    path(r'b2c_report_get/', views.b2c_report_get, name='b2c_report_get'),
    path(r'hsn_report_get/', views.hsn_report_get, name='hsn_report_get'),
    path(r'daily_report_get/', views.daily_report_get, name='daily_report_get'),
    path(r'daily_report_bill_get/', views.daily_report_bill_get, name='daily_report_bill_get'),
    path(r'party_challan_ledger_get/', views.party_challan_ledger_get, name='party_challan_ledger_get'),
    path(r'party_bill_ledger_get/', views.party_bill_ledger_get, name='party_bill_ledger_get'),
    path(r'party_combined_ledger_get/', views.party_combined_ledger_get, name='party_combined_ledger_get'),
	path(r'due_list_bill_get/', views.due_list_bill_get, name='due_list_bill_get'),
]