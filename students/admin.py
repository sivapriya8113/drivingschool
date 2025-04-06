from django.contrib import admin
from django.contrib import messages
from .models import Student, Vehicle, StudentPackage, Trainer, TrainingPackage, TrainingSession, Tutorial, Course
from .utils import assign_sessions  # Import the assignment function

# Action to assign sessions
@admin.action(description="Assign sessions to selected student packages")
def assign_training_sessions(modeladmin, request, queryset):
    for package in queryset:
        if not package.payment_status:
            messages.warning(request, f"⏳ Skipped {package} — Payment not completed.")
            continue
        try:
            assign_sessions(package)
            messages.success(request, f"✅ Sessions assigned for {package}")
        except Exception as e:
            messages.error(request, f"❌ Failed to assign for {package}: {e}")

# Inline TrainingSessions inside StudentPackage
class TrainingSessionInline(admin.TabularInline):
    model = TrainingSession
    extra = 0

# Customize StudentPackage Admin
@admin.register(StudentPackage)
class StudentPackageAdmin(admin.ModelAdmin):
    list_display = ('student', 'package', 'payment_status', 'remaining_sessions')
    inlines = [TrainingSessionInline]
    actions = [assign_training_sessions]  # ✅ Added custom action here

# Register other models normally
admin.site.register(Vehicle)
admin.site.register(Trainer)
admin.site.register(TrainingPackage)
admin.site.register(Tutorial)
admin.site.register(Course)
admin.site.register(Student)



# admin.py or forms.py
from django import forms

class TrainingSessionAdminForm(forms.ModelForm):
    class Meta:
        model = TrainingSession
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(TrainingSessionAdminForm, self).__init__(*args, **kwargs)
        # Filter students who have purchased a package
        eligible_students = Student.objects.filter(
    packages__payment_status=True,
    packages__remaining_sessions__gt=0
).distinct()

        self.fields['student'].queryset = eligible_students



@admin.register(TrainingSession)
class TrainingSessionAdmin(admin.ModelAdmin):
    form = TrainingSessionAdminForm
    list_display = ('student', 'trainer', 'session_date', 'time_slot', 'completed')
    list_filter = ('trainer', 'session_date', 'completed')
    search_fields = ('student__user__username', 'trainer__user__username')
