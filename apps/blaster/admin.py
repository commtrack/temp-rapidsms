#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.contrib import admin
from blaster.models import *

admin.site.register(MessageBlast)
admin.site.register(BlastableMessage)
admin.site.register(BlastedMessage)
admin.site.register(BlastResponse)

