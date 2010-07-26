#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.conf.urls.defaults import *
import schools.views as views


urlpatterns = patterns('',
    url(r'^schools/?$', views.dashboard),
    url(r'^schools/list/?$', views.schools),
    url(r'^schools/map/?$', views.map),
    url(r'^schools/xml/?$', views.xml),
    url(r'^schools/headmasters/?$', views.headmasters),
    url(r'^schools/(?P<id>\d*)/?$', "schools.views.single_school", name="single_school"),
    url(r'^schools/(?P<id>\d*)/xml/?$', "schools.views.single_school_xml", name="single_school_xml"),
    url(r'^schools/message/(?P<id>\d*)/?$', views.message),
)
