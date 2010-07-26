from datetime import datetime
from django.db import models
from django.db.models import Q
from reporters.models import Reporter, PersistantConnection, Location 
from locations.models import Location
from scheduler.models import EventSchedule, set_weekly_event
from logger.models import IncomingMessage

# identifiers for state transitions
SAWA_CODE = 'sawa'
SHIDA_CODE = 'shida'
UNSUBSCRIBE_CODE = 'unsubscribed'
INACTIVE_CODE = 'inactive'

class Site(Location):
    """ This model represents a WelTel site """
    # fields TBD
    pass

class WeltelUser(Reporter):
    """ This model represents any weltel users """
    # subscribed is False, until the user provides a valid connection
    subscribed = models.BooleanField(default=False)
    class Meta:
        abstract = True
        
    def unsubscribe(self):
        self.set_subscribe(False)

    def set_subscribe(self, bool):
        if self.subscribed != bool:
            self.subscribed = bool
            self.save()
            if not self.subscribed:
                # delete all scheduled alerts for this user
                schedules = EventSchedule.objects.filter(callback_args__contains=self.id).delete()
                
    def messages(self, or_query=None, order_by=None):
        filters = None
        for conn in self.connections.all():
            if filters is None:
                filters = Q(identity=conn.identity, backend=conn.backend)
            else:
                filters = filters | Q(identity=conn.identity, \
                                      backend=conn.backend)
        if filters is None: return None
        if or_query is None:
            messages = IncomingMessage.objects.filter(filters)
        else: 
            messages = IncomingMessage.objects.filter(filters|or_query)
        if order_by is not None:
            return messages.order_by(order_by)
        return messages

class Nurse(WeltelUser):
    """ This model represents a nurse for WelTel. 
    
    """  
    # Nurses can be associated with zero or more locations
    # this could get very confusing, since 'reporters' has its own 'location'
    # field. But that's a hack, so we shouldn't use it.
    sites = models.ManyToManyField(Site, null=True)

    def __unicode__(self):
        if self.alias: return self.alias
        return self.id
    
    def subscribe(self):
        super(Nurse, self).set_subscribe(True)

MALE = 'm'
FEMALE = 'f'
GENDER_CHOICES=(
    (MALE, 'male'),
    (FEMALE,'female')
)

class Patient(WeltelUser):
    """ This model represents a patient for WelTel """
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True)
    state = models.ForeignKey("PatientState")
    active = models.BooleanField(default=True)
    site = models.ForeignKey(Site)
    # this is rather crude. TODO - change into some sort of dynamic logging system
    date_registered = models.DateTimeField(null=False, default=datetime.now )
    # a db table to tag all incoming messages having to do with this patient
    # note that this is both messages sent by this patient as well as
    # messages *about* this patient
    related_messages = models.ManyToManyField(IncomingMessage, null=True)
    
    def __unicode__(self):
        if self.alias: return self.alias
        if self.connection: return self.connection.identity
        return self.id
        
    # make 'patient_id' an alias for reporter.alias
    def _get_patient_id(self):
        return self.alias
    def _set_patient_id(self, value):
        self.alias = value
    patient_id = property(_get_patient_id, _set_patient_id)
    
    def register_event(self, code, issuer=None, notes=None):
        event = EventType.objects.get(code=code)
        if event.next_state is not None:
            self.state = event.next_state
        self.save()
        if issuer is None: issuer = self.alias
        EventLog(event=event, patient=self, triggered_by=unicode(issuer), notes=notes).save()
        return event

    def subscribe(self):
        if self.subscribed:
            return
        super(Patient, self).set_subscribe(True)
        # set up weekly mambo schedule for friday @ 12:30 pm
        scheds = EventSchedule.objects.filter(callback="weltel.callbacks.send_mambo", \
                                              callback_args__contains=str(self.id))
        if len(scheds) == 0:
            set_weekly_event("weltel.callbacks.send_mambo", day=2, hour=16, \
                             minute=30, callback_args=[self.id])

    def unsubscribe(self):
        self.register_event(UNSUBSCRIBE_CODE)
        super(Patient, self).unsubscribe()

class PatientState(models.Model):
    code = models.CharField(max_length=15)
    name = models.CharField(max_length=63, null=True, blank=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    
    def __unicode__(self):
        return self.name if self.name else self.code
    
# events in a patient's history
# - can be associated with a state transition
class EventType(models.Model):
    code = models.CharField(max_length=15)
    name = models.CharField(max_length=63, null=True, blank=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    # if specified, next_state determines the next state for the patient
    next_state = models.ForeignKey(PatientState, null=True, blank=True)

    def __unicode__(self):
        return self.name if self.name else self.code

class ProblemType(EventType):
    """ Patient reports a problem """
    class Meta:
        abstract = True
            
class OutcomeType(EventType):
    """ Nurse reports an outcome """
    class Meta:
        abstract = True

class EventLog(models.Model):
    event = models.ForeignKey(EventType)
    date = models.DateTimeField(null=False, default=datetime.now )
    patient = models.ForeignKey(Patient)
    # can be triggered by patient, nurse, admin, IT, etc.
    # through sms, webui, etc.
    triggered_by = models.CharField(max_length=63, null=True)
    notes = models.CharField(max_length=160, null=True)
    active = models.BooleanField(default=True)
    subscribed = models.BooleanField(default=True)

    class Meta:
        get_latest_by = 'date'
    
    def __unicode__(self):
        return self.event.name if self.event.name else self.event.code

