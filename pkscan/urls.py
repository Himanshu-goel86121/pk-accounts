"""pkscan URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include

from login.forms import LoginForm

urlpatterns = [
    path('admin/', admin.site.urls),
    url(r'^login/$', auth_views.LoginView.as_view(), {'template_name': 'login.html', 'authentication_form': LoginForm}, name='login'),
    url(r'^logout/$', auth_views.LogoutView.as_view(), {'next_page': '/login'}, name='logout'),
    url(r'', include('login.urls')),
    url(r'^items_group/', include('items_group.urls'), name='items_group/'),
    url(r'^user/', include('users.urls'), name='user/'),
    url(r'^client/', include('client.urls'), name='client/'),
    url(r'^pchallan/', include('pchallan.urls'), name='pchallan/'),
    url(r'^bill/', include('bill.urls', namespace="bill"), name='bill/'),
    url(r'^fchallan/', include('fchallan.urls'), name='fchallan/'),
    url(r'^items/', include('items.urls'), name='items/'),
    url(r'^logs/', include('logs.urls'), name='logs/'),
    url(r'^slips/', include('slips.urls'), name='slips/'),
    url(r'^report/', include('report.urls'), name='report/'),
    url(r'^payment/', include('payment.urls'), name='payment/'),
    url(r'^password_reset/$', auth_views.PasswordResetView.as_view(), {'template_name': 'password_reset.html'},
        name='password_reset'),
    url(r'^password_reset/done/$', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    url(r'^reset/done/$', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]
