from django.urls import path

from . import views

app_name = 'slips_app'
urlpatterns = [
    path(r'add/', views.slips_add, name='add_page'),
    path(r'submit_slip', views.submit_slip, name='submit_slip'),
    path(r'slip_dashboard', views.slip_dashboard_page, name="slip_dashboard"),
    path(r'get_slip_jobs', views.get_slip_jobs, name="get_slip_jobs"),
    path(r'update_status', views.update_status, name="update_status"),
    path(r'modify', views.slips_modify, name="modify_page"),
    path(r'delete', views.slips_delete, name="delete_page"),
    path(r'submit_slip_modify', views.submit_slip_modify, name='submit_slip_modify'),
    path(r'submit_slip_delete', views.submit_slip_delete, name='submit_slip_delete'),
    path(r'print_slip_jobs', views.print_slip_jobs, name='print_slip_jobs'),
]
