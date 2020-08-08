# -*- coding: utf-8 -*-
"""
Created on Sun May 20 17:28:44 2018

@author: Himanshu
"""

from django.conf import settings
from django.contrib import auth
from datetime import datetime, timedelta
from django.utils.deprecation import MiddlewareMixin

class AutoLogout(MiddlewareMixin):
    def process_request(self, request):
        if not request.user.is_authenticated :
            #Can't log out if not logged in
            return
        try:
            if datetime.now() - datetime.strptime(request.session['last_touch'],"%Y-%m-%d %H:%M:%S") > timedelta( 0, settings.AUTO_LOGOUT_DELAY * 60, 0):
                auth.logout(request)
                del request.session['last_touch']
                return
        except KeyError:
            pass
        request.session['last_touch'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")