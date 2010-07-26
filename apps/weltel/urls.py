#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import os
from django.conf.urls.defaults import *
import weltel.views as views
from weltel.models import Patient, Nurse
from weltel.forms import PatientForm, NurseForm

urlpatterns = patterns('',
    url(r'^$',                      views.index),
    url(r'^site/(?P<pk>\d+)$',             views.site),
    url(r'^patient/(?P<pk>\d+)$',          views.patient, name="patient_history"),
    url(r'^patient/(?P<pk>\d+)/messages$', views.patient_messages, name="patient_messages"),
    url(r'^nurse/(?P<pk>\d+)$',            views.nurse),
    url(r'^patient/(?P<pk>\d+)/edit$',     views.edit_klass, \
        {'klass':Patient, 'klass_form':PatientForm}),
    url(r'^nurse/(?P<pk>\d+)/edit$',       views.edit_klass, \
        {'klass':Nurse, 'klass_form':NurseForm}),
)
