#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.conf.urls.defaults import *
import blaster.views as views


urlpatterns = patterns('',
    url(r'^blaster/?$', views.new),
    url(r'^blaster/list/?$', views.list),
    url(r'^blaster/(?P<id>\d*)/?$', 'blaster.views.single_blast', name="single_blast"),
)
