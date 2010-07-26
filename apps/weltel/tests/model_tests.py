from rapidsms.tests.scripted import TestScript
from reporters.models import PersistantBackend
from scheduler.models import EventSchedule
import reporters.app as reporters_app
import weltel.app as weltel_app
from weltel.models import *
from weltel.formslogic import WeltelFormsLogic

class TestModels (TestScript):
    apps = (reporters_app.App, weltel_app.App )
    
    def setUp(self):
        TestScript.setUp(self)
    
    def test_patient_creation(self):
        wfl = WeltelFormsLogic()
        backend = PersistantBackend.objects.get_or_create(slug=self.backend.slug)[0]
        patient, response = wfl.get_or_create_patient("BA1-1-08", \
                                                      phone_number="1250", \
                                                      backend=backend, 
                                                      gender="f", 
                                                      date_registered=datetime.now())
        try:
            e = EventSchedule.objects.get(callback="weltel.callbacks.send_mambo",
                                          callback_args=[patient.id])
        except EventSchedule.DoesNotExist:
            self.fail('Mambo schedule not created with new patient')
        except EventSchedule.MultipleObjectsReturned:
            self.fail('Multiple mambo schedules created for a single patient')
            
    def test_multiple_patient_creation(self):
        wfl = WeltelFormsLogic()
        backend = PersistantBackend.objects.get_or_create(slug=self.backend.slug)[0]
        patient, response = wfl.get_or_create_patient("BA1-1-08", \
                                                      phone_number="1250", \
                                                      backend=backend, 
                                                      gender="f", 
                                                      date_registered=datetime.now())
        patient, response = wfl.get_or_create_patient("BA1-1-08", \
                                                      phone_number="1250", \
                                                      backend=backend, 
                                                      gender="f", 
                                                      date_registered=datetime.now())
        patient, response = wfl.get_or_create_patient("BA1-1-08", \
                                                      phone_number="1250", \
                                                      backend=backend, 
                                                      gender="f", 
                                                      date_registered=datetime.now())
        try:
            e = EventSchedule.objects.get(callback="weltel.callbacks.send_mambo",
                                          callback_args=[patient.id])
        except EventSchedule.DoesNotExist:
            self.fail('Mambo schedule not created with new patient')
        except EventSchedule.MultipleObjectsReturned:
            self.fail('Multiple mambo schedules created for a single patient')

    def test_nurse_subscription(self):
        wfl = WeltelFormsLogic()
        backend = PersistantBackend.objects.get_or_create(slug=self.backend.slug)[0]
        nurse, response = wfl.get_or_create_nurse(site_code="BA1-1", \
                                                  phone_number="1252", \
                                                  backend=backend)
        self.assertTrue(nurse.subscribed==True)
        nurse.unsubscribe()
        self.assertTrue(nurse.subscribed==False)
        nurse.subscribe()
        self.assertTrue(nurse.subscribed==True)
