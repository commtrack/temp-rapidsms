#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import re
from rapidsms.i18n import ugettext_noop as _
from form.formslogic import FormsLogic
from reporters.models import PersistantConnection
from scheduler.models import set_weekly_event
from weltel.models import Site, Patient, PatientState, Nurse, MALE, FEMALE
from weltel.util import site_code_from_patient_id

REGISTER_COMMAND = _("To register, please refer to your information card.")
NURSE_COMMAND = _("To register, please refer to your information card.")

#TODO - add basic check for when people submit fields in wrong order
#TODO - wrap the validation and actions in pretty wrapper functions

class WeltelFormsLogic(FormsLogic):
    ''' This class will hold the Weltel-specific forms logic. '''    
    
    def validate(self, *args, **kwargs):
        message = args[0]
        form_entry = args[1]
        data = form_entry.to_dict()

        if form_entry.form.code.abbreviation == "register":
            ret = self.is_patient_invalid(data["patient_id"], \
                                          data["gender"], data["phone_number"])
            if not ret: 
                # all fields were present and correct, so copy them into the
                # form_entry, for "actions" to pick up again without re-fetching
                form_entry.reg_data = data
            return ret
        elif form_entry.form.code.abbreviation == "nurse":
            ret = self.is_nurse_invalid(data["site_code"])
            if not ret: 
                # all fields were present and correct, so copy them into the
                # form_entry, for "actions" to pick up again without re-fetching
                form_entry.nurse_data = data
            return ret

    def actions(self, *args, **kwargs):
        message = args[0]
        form_entry = args[1]
        # language = get_language_code(message.persistant_connection)
        
        if form_entry.form.code.abbreviation == "register":
            if len(form_entry.reg_data["phone_number"])>0:
                phone_number = form_entry.reg_data["phone_number"]
            else: 
                phone_number = message.persistant_connection.identity
            gender = None
            if "gender" in form_entry.reg_data:
                if form_entry.reg_data["gender"].lower().startswith('m'):
                    gender = MALE
                elif form_entry.reg_data["gender"].lower().startswith('f'):
                    gender = FEMALE
            #registered=message.date
            patient, response = self.get_or_create_patient(form_entry.reg_data["patient_id"], \
                                       phone_number=phone_number, \
                                       backend= message.persistant_connection.backend, 
                                       gender=gender)
            patient.related_messages.add(message.persistent_msg)
            message.respond(response)
        elif form_entry.form.code.abbreviation == "nurse":
            site_code =  form_entry.nurse_data["site_code"]
            phone_number = message.persistant_connection.identity
            backend = message.persistant_connection.backend
            nurse, response = self.get_or_create_nurse(site_code, phone_number, backend)
            message.respond(response)

    def is_patient_invalid(self, patient_id, gender=None, phone_number=None):
        if len(patient_id) == 0:
            return [_("Missing 'patient_id'. ") + REGISTER_COMMAND ]
        try:
            site_code = site_code_from_patient_id(patient_id)
        except ValueError:
            return [_("Patient (%(id)s) not recognized") % \
                    {"id" : patient_id}]
        try:
            Site.objects.get(code__iexact=site_code)
        except Site.DoesNotExist:
            response = _("Site %(code)s does not exist") % {"code": site_code }
            return [response]
        if len(gender) > 0:
            if not gender.lower().startswith('m') and not gender.lower().startswith('f'):
                return [_("Invalid gender %(gender)s") % {"gender" : gender}]
        if len(phone_number) > 0:
            if not re.match(r"^\+?\d+$", phone_number):
                return [_("Invalid phone number %(num)s") % {"num" : phone_number}]
        return False
    
    def is_nurse_invalid(self, site_code):
        if len(site_code) == 0:
            return [_("Missing 'site_code'. ") + NURSE_COMMAND ]
        try:
            Site.objects.get(code__iexact=site_code)
        except Site.DoesNotExist:
            response = _("Site %(code)s does not exist") % {"code": site_code }
            return [response]
        return False

    def get_or_create_patient(self, patient_id, phone_number=None, \
                              backend=None, gender=None, date_registered=None):
        response = ''
        try:
            patient = Patient.objects.get(alias__iexact=patient_id)
            response = _("Patient %(id)s reregistered ") % {"id": patient_id }
            if not patient.subscribed:
                patient.subscribe()
            p_created = False
        except Patient.DoesNotExist:
            patient = Patient(alias=patient_id)
            response = _("Patient %(id)s registered ") % {"id": patient_id }
            p_created = True
        site_code = site_code_from_patient_id(patient_id)
        try:
            patient.site = Site.objects.get( code__iexact=site_code )
        except Site.DoesNotExist:
            response = _("Site %(code)s does not exist") % {"code": site_code }
            return (patient, response)
        if gender: patient.gender = gender
        patient.state = PatientState.objects.get(code='default')
        if date_registered: 
            patient.date_registered = date_registered
        patient.save()

        if phone_number is None:
            return (patient, response)
        # save connections
        conn, c_created = PersistantConnection.objects.get_or_create(\
                          identity= phone_number, backend=backend)
        if conn.reporter is None:
            response = response + \
                       _("with new number %(num)s") % \
                       {"num": phone_number}
        else:
            response = response + \
                       _("with existing number %(num)s") % \
                       {"num": phone_number }
            if conn.reporter.alias != patient.alias:
                response = response + _(" (from patient %(old_id)s)") % \
                                      {"old_id": conn.reporter.alias }
        conn.reporter = patient
        conn.save()
        patient.set_preferred_connection( conn )
        # you can only subscribe the patient once you have established 
        # their preferred connection
        patient.subscribe()
        return (patient, response)

    def get_or_create_nurse(self, site_code, phone_number, backend):
        try:
            site = Site.objects.get(code__iexact=site_code)
        except Site.DoesNotExist:
            response = _("Site %(code)s does not exist") % {"code": site_code }
            return None, response
        # for now, set unique id to be phone number
        nurse, n_created = Nurse.objects.get_or_create(alias= phone_number)
        nurse.sites.add(site)
        if n_created:
            response = _("Nurse registered") % {"id": nurse.alias }
        else:
            response = _("Nurse reregistered") % {"id": nurse.alias }
        
        # save connections
        conn, c_created = PersistantConnection.objects.get_or_create(identity= phone_number, \
                                                   backend= backend)
        if conn.reporter is None:
            response = response + (_(" with new number %(num)s") % \
                                   {"num": phone_number})
        else:
            response = response + (_(" with existing number %(num)s") % \
                            {"num": phone_number})                    
            if nurse.alias != conn.reporter.alias:
                response = response + (_(" reregistered from %(old_id)s") % \
                            {"id": nurse.alias, "old_id": conn.reporter.alias }) 
        conn.reporter = nurse
        conn.save()
        nurse.subscribe()
        return nurse, response
