import logging
from datetime import datetime, timedelta
from rapidsms.message import Message
from rapidsms.i18n import ugettext_noop as _
from logger.models import IncomingMessage
from weltel.models import Site, Nurse, Patient, PatientState, EventLog
from weltel.models import UNSUBSCRIBE_CODE, INACTIVE_CODE

######################
# Callback Functions #
######################

def send_mambo(router, patient_id):
    response = "Mambo?"
    logging.info("Sending: %s" % response)
    connection = Patient.objects.get(id=patient_id).connection
    be = router.get_backend(connection.backend.slug)
    be.message(connection.identity, response).send()

def shida_report(router, nurse=None):
    # list of 'shida' patients for each site, or for a specific nurse if given
    sites = nurse.sites.all() if nurse is not None else Site.objects.all()
    for site in sites:
        shida = PatientState.objects.get(code='shida')
        # get all active patients who responded shida or are in the default state
        patients = Patient.objects.filter(site=site).filter(state=shida).exclude(active=False).exclude(subscribed=False)
        # generate report
        report = ''
        for patient in patients:
            # take the last '1' from Patient ID BA3-2-1
            id = patient.patient_id.rsplit('-',1)[-1]
            if hasattr(patient,'connection') and patient.connection is not None:
                report = report + "%(id)s-%(identity)s " % \
                                  {'id':id,
                                   'identity': patient.connection.identity}
            else:
                report = report + "%(id)s-None " % {'id':id }
        # send report to given nurse, or if nurse not supplied, 
        # all nurses registered for that site
        nurses = [nurse] if nurse is not None else Nurse.objects.filter(sites=site).filter(subscribed=True)
        for n in nurses:
            be = router.get_backend(n.connection.backend.slug)
            if report:
                be.message(n.connection.identity, report).send()
            else:
                be.message(n.connection.identity, _("No problem patients")).send()


def mark_inactive(router, timeout_weeks):
    timeout_interval = timedelta(weeks=timeout_weeks)
    timeout = datetime.now() - timeout_interval
    # check if patients have not been seen in a while
    patients = Patient.objects.all()
    active = patients.filter(active=True).filter(subscribed=True)
    for patient in active:
        active = False
        # check a) no messages in X time from any of their connections
        for conn in patient.connections.all():
            try:
                log = IncomingMessage.objects.latest()
            except IncomingMessage.DoesNotExist:
                if patient.date_registered > timeout:
                    active = True
                # no messages received yet. TODO: check for the signup date of the patient.
                # once we start logging sign-up dates, that is. 
            else:
                if log.received > timeout:
                    active = True
                    continue
        # check b) no status updates from nurse
        try:
            last_touched = EventLog.objects.filter(patient=patient).latest()
        except EventLog.DoesNotExist:
            pass
        else:
            if last_touched.date > timeout:
                active = True
        if active == False:
            patient.register_event(INACTIVE_CODE)
            patient.active = False
            patient.save()
    return

def other_report(router, nurse=None):
    # list of 'inactive' and unsubscribed patients for each site
    sawa = PatientState.objects.get(code='sawa')
    timeout_interval = timedelta(days=1)
    timeout = datetime.now() - timeout_interval
    sites = nurse.sites.all() if nurse is not None else Site.objects.all()
    
    for site in sites:
        report = ''
        # get all active patients who unsubscribed today
        report_unsubscribed = ''
        unsubscribed = Patient.objects.filter(site=site).filter(active=True).filter(subscribed=False)
        for p in unsubscribed:
            unsubscribe_event = EventLog.objects.filter(patient=p).filter(event__code=UNSUBSCRIBE_CODE).latest()
            if not unsubscribe_event:
                logging.error("Patient is unsubscribed without unsubscribe event!")
            elif unsubscribe_event.date > timeout:
                id = p.patient_id.rsplit('-',1)[-1]
                if hasattr(p, 'connection') and p.connection is not None:
                    report_unsubscribed = report_unsubscribed + "%s-%s " % \
                            (id, p.connection.identity)
                else:
                    report_unsubscribed = report_unsubscribed + "%s-None " % (id)
        # get patients who were marked 'inactive' today
        report_inactive = ''
        inactive = Patient.objects.filter(site=site).filter(active=False)
        for p in inactive:
            inactivated_event = EventLog.objects.filter(patient=p).filter(event__code=INACTIVE_CODE).latest()
            if not inactivated_event:
                logging.error("Patient is inactivated without inactivate event!")
            elif inactivated_event.date > timeout:
                id = p.patient_id.rsplit('-',1)[-1]
                if hasattr(p, 'connection') and p.connection is not None:
                    report_inactive = report_inactive + "%s-%s " % (id, \
                             p.connection.identity)
                else:
                    report_inactive = report_inactive + "%s-None " % (id)                    

        if report_unsubscribed:
            report = report + "Unsubscribed: " + report_unsubscribed
        if report_inactive:
            report = report + "Inactive: " + report_inactive
        
        # send report to all nurses registered for that site
        nurses = [nurse] if nurse is not None else Nurse.objects.filter(sites=site).filter(subscribed=True)
        for n in nurses:
            be = router.get_backend(n.connection.backend.slug)
            if report:
                be.message(n.connection.identity, report).send()
            else:
                be.message(n.connection.identity, _("No patients unsubscribed or were marked inactive today.")).send()

