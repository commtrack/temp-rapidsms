import time
from datetime import datetime, timedelta
from reporters.models import Reporter, PersistantBackend
from rapidsms.tests.scripted import TestScript
from weltel.models import *
import logger.app as logger_app
import reporters.app as reporters_app
import scheduler.app as scheduler_app
import weltel.app as weltel_app
import form.app as form_app
from weltel.formslogic import WeltelFormsLogic
from weltel.app import SAWA_CODE, SHIDA_CODE

class TestSMS (TestScript):
    apps = (logger_app.App, reporters_app.App, form_app.App, scheduler_app.App, weltel_app.App )
    
    def setUp(self):
        TestScript.setUp(self)
    
    testFromLocalNum = """
        +2547111222333 > well register BA1-1-10
        +2547111222333 < Patient BA1-1-10 registered with new number +2547111222333
        +2547111222333 > 07111222333 sawa
        +2547111222333 < Asante
        +2547111222333 > 07111222333 shida notes
        +2547111222333 < Asante. Tutakupigia simu hivi karibuni.
    """

    testFromNumErr2 = """
        +2547111222333 > 0711122237 shida notes
        +2547111222333 < Poorly formatted phone number. Do not use spaces or dashes, e.g. +254712222333.
    """
    
    testFromIntlNum = """
        +2547111222333 > well register BA1-1-10
        +2547111222333 < Patient BA1-1-10 registered with new number +2547111222333
        +2547111222333 > +2547111222333 sawa
        +2547111222333 < Asante
        +2547111222333 > +2547111222333 shida notes
        +2547111222333 < Asante. Tutakupigia simu hivi karibuni.
    """

    testOutcomeToOtherPhone = """
        1248 > well register BA1-1-07 male
        1248 < Patient BA1-1-07 registered with new number 1248
        1299 > BA1-1-07 sawa
        1299 < Asante
        1299 > BA1-1-07 2
        1299 < Please respond 'sawa' or 'shida', followed by any additional comments you have.
    """
    
    test_unknown_patient_other = """
        # (%s)\s*(.*)" % PATIENT_ID_REGEX)
        1240 > XY-1-0001 1
        1240 < This number is not registered. To register, please refer to your information card.
        """
    
    test_unknown_site_patient = """
        # new patient - these have only been tested with empty db (no forms). may break once populated.
        1240 > well register nonexistantsite/1 female
        1240 < Error. Site nonex does not exist
        """
    
    test_unknown_site_nurse = """
        # new nurse - these have only been tested with empty db (no forms). may break once populated.
        1240 > well nurse nonexistantsite
        1240 < Error. Site nonexistantsite does not exist
        """
    
    test_unregistered = """
        1233 > asdf
        1233 < This number is not registered. To register, please refer to your information card.
    """
    
    test_patient_registration = """
        # new patient new number
        1234 > well register BA1-1-01 female
        1234 < Patient BA1-1-01 registered with new number 1234
        # new patient old number
        1236 > well register BA1-1-02 f 1234
        1236 < Patient BA1-1-02 registered with existing number 1234 (from patient BA1-1-01)
        # old patient new number
        1234 > well register BA1-1-01 male 1235
        1234 < Patient BA1-1-01 reregistered with new number 1235
        # old patient old number belonging to patient
        1237 > well register BA1-1-01 m 1235
        1237 < Patient BA1-1-01 reregistered with existing number 1235
        # old patient old number not belonging to patient
        1234 > well register BA1-1-01 FEMALE
        1234 < Patient BA1-1-01 reregistered with existing number 1234 (from patient BA1-1-02)
        1234 > well unsubscribe
        1234 < Kwaheri
        1234 > well subscribe
        1234 < Karibu
        """
        
    test_patient_registration_err = """
        1238 > well register
        1238 < This number is not registered. To register, please refer to your information card.
        1238 > well register 1
        1238 < Error. Patient (1) not recognized
        1238 > well register f BA1-1-01
        1238 < Error. Patient (f) not recognized
        """
    
    test_nurse_registration = """
        # new nurse
        1240 > well nurse BA1-1
        1240 < Nurse registered with new number 1240
        # old
        1240 > well nurse BA1-1
        1240 < Nurse reregistered with existing number 1240
        # new nurse old number
        1241 > well register BA1-1-03 f
        1241 < Patient BA1-1-03 registered with new number 1241
        1241 > well nurse BA1-1
        1241 < Nurse registered with existing number 1241 reregistered from BA1-1-03
        1241 > well unsubscribe
        1241 < Kwaheri
        1241 > well subscribe
        1241 < Karibu
        """
        
    test_nurse_registration_err = """
        # new nurse
        1240 > well nurse
        1240 < This number is not registered. To register, please refer to your information card.
        """
        
    test_commands = """
        1242 > well register BA1-1-04 m
        1242 < Patient BA1-1-04 registered with new number 1242
        1243 > well phone BA1-1-04
        1243 < Phone number 1243 has been registered to patient BA1-1-04
        1244 > well phone BA1-1-04
        1244 < Phone number 1244 has been registered to patient BA1-1-04
        1244 > well phones
        1244 < 1242, 1243, 1244
        1244 > well set phone
        1244 < Patient BA1-1-04 default phone set to 1244
        1244 > well get phone
        1244 < Patient BA1-1-04 default phone is 1244
        1242 > well set phone
        1242 < Patient BA1-1-04 default phone set to 1242
        1242 > well get phone
        1242 < Patient BA1-1-04 default phone is 1242
        """
        
    testSawaShida = """
        1245 > well register BA1-1-05 female
        1245 < Patient BA1-1-05 registered with new number 1245
        1245 > sawa
        1245 < Asante
        1245 > shida
        1245 < Asante. Tutakupigia simu hivi karibuni.
        1245 > shida 1
        1245 < Asante. Tutakupigia simu hivi karibuni. ('pain (abdominal)')
        1245 > Unrecognized randomness
        1245 < Please respond 'sawa' or 'shida', followed by any additional comments you have.
        """
        
    testOutcome = """
        1246 > well nurse BA1-1
        1246 < Nurse registered with new number 1246
        1247 > well register BA1-1-06 female
        1247 < Patient BA1-1-06 registered with new number 1247
        1248 > well register BA1-1-07 male
        1248 < Patient BA1-1-07 registered with new number 1248
        1246 > BA1-1-06 1
        1246 < Patient BA1-1-06 updated to 'pain (abdominal)'
        1246 > BA1-1-07 2
        1246 < Patient BA1-1-07 updated to 'pain'
        """
    
    testShidaReport = """
        1260 > well register BA1-1-011 female
        1260 < Patient BA1-1-011 registered with new number 1260
        1261 > well register BA1-1-012 female
        1261 < Patient BA1-1-012 registered with new number 1261
        1262 > well nurse BA1-1
        1262 < Nurse registered with new number 1262
        1262 > well report shida
        1262 < No problem patients
        1260 > shida
        1260 < Asante. Tutakupigia simu hivi karibuni.
        1261 > shida
        1261 < Asante. Tutakupigia simu hivi karibuni.
        1262 > well report shida
        1262 < 011-1260 012-1261
        1260 > sawa
        1260 < Asante
        1262 > well report shida
        1262 < 012-1261
        1261 > sawa
        1261 < Asante
        1262 > well report shida
        1262 < No problem patients
        1260 > shida
        1260 < Asante. Tutakupigia simu hivi karibuni.
        1262 > well report shida
        1262 < 011-1260
        1261 > shida 2
        1261 < Asante. Tutakupigia simu hivi karibuni. ('pain')
        1262 > well report shida
        1262 < 011-1260 012-1261
        1261 > sawa
        1261 < Asante
        1262 > well report shida
        1262 < 011-1260
        """
    
    testEmptyOtherReport = """
        1262 > well nurse BA1-1
        1262 < Nurse registered with new number 1262        
        1262 > well report other
        1262 < No patients unsubscribed or were marked inactive today.       
    """
    
    testOtherReport = """
        1260 > well register BA1-1-011 female
        1260 < Patient BA1-1-011 registered with new number 1260
        1260 > well unsubscribe
        1260 < Kwaheri
        1261 > well register BA1-1-012 female
        1261 < Patient BA1-1-012 registered with new number 1261
        1261 > well unsubscribe
        1261 < Kwaheri
        1262 > well nurse BA1-1
        1262 < Nurse registered with new number 1262
        1262 > well report other
        1262 < Unsubscribed: 011-1260 012-1261
        1261 > well subscribe
        1261 < Karibu
        1262 > well report other
        1262 < Unsubscribed: 011-1260
        1261 > well inactive
        1261 < Kwaheri
        1262 > well report other
        1262 < Unsubscribed: 011-1260 Inactive: 012-1261
        """
    
    testShidaReportNoConnection = """
        1260 > well register BA1-1-011
        1260 < Patient BA1-1-011 registered with new number 1260
        1260 > well unsubscribe
        1260 < Kwaheri
        1260 > well register BA2-1-011
        1260 < Patient BA2-1-011 registered with existing number 1260 (from patient BA1-1-011)
        1262 > well nurse BA1-1
        1262 < Nurse registered with new number 1262
        1262 > well report other
        1262 < Unsubscribed: 011-None
        """
        
    testOtherReportNoConnection = """
        1260 > well register BA1-1-011
        1260 < Patient BA1-1-011 registered with new number 1260
        1260 > shida
        1260 < Asante. Tutakupigia simu hivi karibuni.
        1260 > well register BA2-1-011
        1260 < Patient BA2-1-011 registered with existing number 1260 (from patient BA1-1-011)
        1262 > well nurse BA1-1
        1262 < Nurse registered with new number 1262
        1262 > well report shida
        1262 < 011-None
        """
