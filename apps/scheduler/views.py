#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from rapidsms.webui.utils import paginated, render_to_response

from scheduler.models import EventSchedule
from scheduler.forms import ScheduleForm

@login_required
#@permission_required("eventschedule.can_view")
def index(request, template="scheduler/index.html"):
    context = {}
    schedules = EventSchedule.objects.all()
    context['schedules'] = paginated(request, schedules)
    return render_to_response(request, template, context)

@login_required
#@permission_required("eventschedule.can_edit")
def edit(request, pk, template="scheduler/edit.html"):
    context = {}
    schedule = get_object_or_404(EventSchedule, id=pk)
    if request.method == 'POST':
        form = ScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            form.save()
            context['status'] = _("Schedule '%(name)s' successfully updated" % \
                                {'name':schedule.callback} )
        else:
            context['errors'] = form.errors
    else:
        form = ScheduleForm(instance=schedule)
    context['form'] = form
    context['schedule'] = schedule
    return render_to_response(request, template, context)    
