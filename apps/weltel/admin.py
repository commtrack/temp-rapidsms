#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.contrib import admin
from weltel.models import Site, Nurse, Patient, PatientState, EventType

admin.site.register(Site)
admin.site.register(Nurse)
admin.site.register(Patient)
admin.site.register(PatientState)
admin.site.register(EventType)
