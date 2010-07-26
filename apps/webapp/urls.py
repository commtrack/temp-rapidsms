#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.conf.urls.defaults import *
import webapp.views as views

# get the login view from the settings
from rapidsms.webui import settings
    
urlpatterns = patterns('',
    url(r'^$',     views.dashboard),
    url(r'^ping$', views.check_availability),
    url(r'^accounts/login/$', views.login, {"template_name": settings.LOGIN_TEMPLATE }, name="login"),
    url(r'^accounts/logout/$', views.logout, {"template_name": settings.LOGGEDOUT_TEMPLATE }, name="logout"),
    url(r'^i18n/', include('django.conf.urls.i18n')),
)

