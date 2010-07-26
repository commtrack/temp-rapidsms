#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from datetime import datetime, timedelta
from django.db.models import Q
from django.db import connection
from django.utils.translation import ugettext as _
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from rapidsms.webui.utils import paginated, render_to_response
from logger.models import IncomingMessage
from reporters.models import Reporter, PersistantBackend, PersistantConnection
from weltel.models import Site, Nurse, Patient, EventType, EventLog
from weltel.models import SAWA_CODE, SHIDA_CODE

@login_required
def index(request, template="weltel/index.html"):
    context = {}
    sites = Site.objects.all().order_by('name')
    start_of_week = datetime.now()
    # set to monday 00:00
    start_of_week = start_of_week - timedelta(days=start_of_week.weekday(), 
                                              hours=start_of_week.hour, 
                                              minutes=start_of_week.minute)
    
    for site in sites:
        patients = Patient.objects.filter(site=site)
        site.patient_count = patients.count()
        site.nurse_count = Nurse.objects.filter(sites=site).count()
        sawa_patients = patients.filter(state__code=SAWA_CODE)
        shida_patients = patients.filter(state__code=SHIDA_CODE)
        site.sawa_count = sawa_patients.count()
        site.shida_count = shida_patients.count()
        
        sawa_patients_this_week = sawa_patients.filter(active=True).filter(subscribed=True)
        sawa_patients_this_week = sawa_patients_this_week.filter(eventlog__date__gte=start_of_week)
        site.sawa_count_this_week = sawa_patients_this_week.distinct().count()
        shida_patients_this_week = shida_patients.filter(active=True).filter(subscribed=True)
        shida_patients_this_week = shida_patients_this_week.filter(eventlog__date__gte=start_of_week)
        site.shida_count_this_week = shida_patients_this_week.distinct().count()
    context['sites'] = paginated(request, sites)
    #messages = EventLog.objects.select_related().order_by('-received')
    #context.update( format_events_in_context(request, context, messages) )
    return render_to_response(request, template, context)

def site(request, pk, template="weltel/site.html"):
    context = {}
    site = get_object_or_404(Site, id=pk)
    patients = Patient.objects.filter(site=site)
    nurses = Nurse.objects.filter(sites=site)
    context['site'] = site
    context['patients'] = paginated(request, patients)
    context['nurses'] = paginated(request, nurses)
    return render_to_response(request, template, context)

def patient(request, pk, template="weltel/patient.html"):
    patient = get_object_or_404(Patient, id=pk)
    context = {}
    context['patient'] = patient
    logs = get_history_for_patient(patient)
    context['history'] = paginated(request, logs)
    context['phone_numbers'] = [c.identity for c in patient.connections.all()]
    return render_to_response(request, template, context )

def patient_messages(request, pk, template="weltel/patient.html"):
    patient = get_object_or_404(Patient, id=pk)
    context = {}
    context['patient'] = patient
    logs = get_messages_for_patient(patient)
    if logs:
        context['messages'] = paginated(request, logs)
    return render_to_response(request, template, context )

def nurse(request, pk, template="weltel/nurse.html"):
    context = {}
    nurse = get_object_or_404(Nurse, id=pk)
    context['nurse'] = nurse
    logs = nurse.messages(order_by='-received')
    if logs:
        context['logs'] = paginated(request, logs)
    context['phone_numbers'] = [c.identity for c in nurse.connections.all()]
    return render_to_response(request, template, context )

@login_required
def edit_klass(request, klass, klass_form, pk, template="weltel/edit.html"):
    context = {}
    awbject = get_object_or_404(klass, id=pk)
    if request.method == "POST":
        form = klass_form(request.POST, awbject)
        if form.is_valid():
            form.save()
            context['status'] = _("'%(name)s' successfully updated" % \
                                {'name':unicode(awbject)} )
        else:
            context['error'] = form.errors
    else:
        form = klass_form(instance=awbject)
    context['form'] = form
    context['title'] = _("Edit %(name)s") % \
                       {'name':unicode(awbject)}
    return render_to_response(request, template, context)

def get_history_for_patient(patient):
    """ this mother of all SQL statements is designed to get a patient's
    history, meaning a list of all messages that they sent from any
    of their registered phones, as well as all logged events that 
    had to do with them. 
    
    """
    cursor = connection.cursor()
    # Known Bug: This JOIN doesn't take into account messages that were 
    # sent by another phone on behalf of a registered user. Let's see if
    # this is an important enough use case for us to fix later.
    # We'd need to rewrite this query to draw from the patient.related_messages
    # table in addition to the incoming message log
    cursor.execute('''
        (SELECT 
            m.identity AS sender, 
            m.text AS description, 
            m.received AS date
            FROM %(msg_log)s m
            LEFT JOIN %(backend)s b
                ON m.backend=b.slug
            LEFT JOIN %(connection)s c
                ON m.identity=c.identity
                AND b.id=c.backend_id
            LEFT JOIN %(reporter)s r
                ON c.reporter_id=r.id
            WHERE r.id=%(patient_id)s
            )
        UNION ALL
        (SELECT 
            e.triggered_by AS sender, 
            t.description AS description, 
            e.date AS date
            FROM %(event_log)s e
            LEFT JOIN %(event_type)s t
                ON t.id = e.event_id
            WHERE e.patient_id=%(patient_id)s
            )
        ORDER BY date DESC, sender DESC
        ''' % {
            # useful in case we ever change the model names
            'msg_log':IncomingMessage._meta.db_table,
            'connection':PersistantConnection._meta.db_table,
            'backend':PersistantBackend._meta.db_table,
            'reporter':Reporter._meta.db_table,
            'event_log':EventLog._meta.db_table,
            'event_type':EventType._meta.db_table,
            'patient_id':patient.pk,
        })
    return cursor.fetchall()

def get_messages_for_patient(patient):
    """ the difference between this and get_history_for_patient
    is that get_history_for_patient attempts to show only messages
    from a patient as well as state changes, while this function shows
    messages from a patient as well as all messages from anyone
    having anything to do with that patient.
    
    """
    # reverse search the manytomany relationship
    return patient.messages(Q(patient__id=patient.pk), order_by='-received')
 
