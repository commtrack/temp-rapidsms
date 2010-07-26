from django.forms import ModelForm
from weltel.models import Patient, Nurse

class NurseForm(ModelForm):
    class Meta:
        model = Nurse
        fields = ('alias', 'first_name', 'family_name', 'sites')

class PatientForm(ModelForm):
    class Meta:
        model = Patient
        fields = ('alias', 'first_name', 'family_name', 'gender', \
                  'state', 'active', 'subscribed', 'site')
