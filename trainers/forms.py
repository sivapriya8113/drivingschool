from django import forms
from .models import Trainer

class TrainerForm(forms.ModelForm):
    class Meta:
        model = Trainer
        fields = ['user', 'specialization', 'experience', 'availability', 'is_remote']
        
class TrainerProfileForm(forms.ModelForm):
    class Meta:
        model = Trainer
        fields = ['specialization', 'experience', 'availability', 'is_remote']
        # Exclude user as it should be set automatically from the logged-in user

from django import forms
from students.models import Student
from trainers.models import Trainer
from vehicles.models import Vehicle

class StudentAssignmentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['trainer', 'vehicle']  # ✅ includes both trainer & vehicle

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['trainer'].queryset = Trainer.objects.filter(is_active=True)
        self.fields['vehicle'].queryset = Vehicle.objects.filter(is_active=True)
        
        # 🔥 Ensure these fields are not left blank
        self.fields['trainer'].required = True
        self.fields['vehicle'].required = True
        
from django import forms
from students.models import TrainingSession

class TrainingSessionForm(forms.ModelForm):
    class Meta:
        model = TrainingSession
        fields = ['trainer', 'vehicle', 'session_date', 'time_slot', 'notes']