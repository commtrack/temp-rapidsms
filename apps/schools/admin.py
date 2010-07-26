#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.contrib import admin
from schools.models import *

admin.site.register(School)
admin.site.register(SchoolGroup)
admin.site.register(Grade)
admin.site.register(Report)
admin.site.register(GradeReport)
admin.site.register(SchoolTeacherReport)
admin.site.register(SchoolWaterReport)
admin.site.register(BoysAttendenceReport)
admin.site.register(GirlsAttendenceReport)
