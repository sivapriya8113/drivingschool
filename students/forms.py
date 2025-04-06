from django import forms
from .models import Student, TrainingSession
from .models import TrainingPackage

class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['address', 'phone_number', 'emergency_contact', 'student_type']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }

class SessionBookingForm(forms.ModelForm):
    class Meta:
        model = TrainingSession
        fields = ['trainer', 'vehicle', 'session_date', 'time_slot']
        widgets = {
            'session_date': forms.DateInput(attrs={'type': 'date'}),
        }


from django import forms
from .models import Payment, TrainingPackage

class PaymentForm(forms.ModelForm):
    package = forms.ModelChoiceField(
        queryset=TrainingPackage.objects.all(),
        empty_label="Select a Training Package",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Payment
        fields = ['package']


