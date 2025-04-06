from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from trainers.models import Trainer
from vehicles.models import Vehicle


from trainers.models import Trainer
from vehicles.models import Vehicle  # or from trainers.models if TrainerVehicle links to Vehicle

class Student(models.Model):
    STUDENT_TYPES = (
        ('local', 'Local Student'),
        ('remote', 'Remote Student'),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_profile'
    )

    trainer = models.ForeignKey(
        Trainer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='student_set'
    )

    # ✅ Add vehicle assignment
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='student_assignments'
    )

    address = models.TextField()
    phone_number = models.CharField(max_length=15)
    emergency_contact = models.CharField(max_length=15, blank=True, null=True)
    student_type = models.CharField(max_length=10, choices=STUDENT_TYPES, default='local')
    registration_date = models.DateTimeField(auto_now_add=True)

    # ✅ Track whether they purchased a session
    has_purchased_session = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.student_type})"

class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='course_images/', blank=True, null=True)
    category = models.CharField(max_length=100, blank=True)
    level = models.CharField(max_length=50, choices=[('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced')], default='beginner')
    vehicle_type = models.CharField(max_length=10, choices=Vehicle.VEHICLE_TYPES)
    
    def __str__(self):
        return self.title



class Vehicle(models.Model):
    VEHICLE_TYPES = (
        ('car', 'Car'),
        ('scooty', 'Scooty'),
    )
    
    vehicle_number = models.CharField(max_length=20, unique=True)
    model = models.CharField(max_length=100)
    vehicle_type = models.CharField(max_length=10, choices=VEHICLE_TYPES)
    purchased_year = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.model} ({self.vehicle_number})"


class TrainingPackage(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='packages',null=True, blank=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    vehicle_type = models.CharField(max_length=10, choices=Vehicle.VEHICLE_TYPES)
    sessions = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.course.title} - {self.name}"
    

class StudentPackage(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='packages')
    package = models.ForeignKey(TrainingPackage, on_delete=models.CASCADE)
    purchase_date = models.DateTimeField(auto_now_add=True)
    payment_status = models.BooleanField(default=False)
    remaining_sessions = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.student} - {self.package}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if is_new:
            self.remaining_sessions = self.package.sessions
        super().save(*args, **kwargs)

        # Assign sessions only after saving (so `self.pk` is available)
        # if is_new:
        #     from .utils import assign_sessions  # prevent circular import
        #     assign_sessions(self)

class TrainingSession(models.Model):
    TIME_SLOTS = (
        ('morning_1', '7:00 AM - 8:30 AM'),
        ('morning_2', '9:00 AM - 10:30 AM'),
        ('morning_3', '11:00 AM - 12:30 PM'),
        ('afternoon_1', '1:00 PM - 2:30 PM'),
        ('afternoon_2', '3:00 PM - 4:30 PM'),
        ('evening', '5:00 PM - 6:30 PM'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='sessions')
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE, related_name='sessions')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='sessions',null=True,blank=True)
    student_package = models.ForeignKey(StudentPackage, on_delete=models.SET_NULL, null=True, blank=True)
    session_date = models.DateField()
    time_slot = models.CharField(max_length=20, choices=TIME_SLOTS)
    completed = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ('trainer', 'session_date', 'time_slot')
    
    def __str__(self):
        return f"{self.student} - {self.session_date} ({self.get_time_slot_display()})"

class Tutorial(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    content = models.TextField()
    video_url = models.URLField(blank=True, null=True)
    visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title

class Attendance(models.Model):
    session = models.OneToOneField(TrainingSession, on_delete=models.CASCADE, related_name='attendance')
    present = models.BooleanField(default=False)
    check_in_time = models.TimeField(null=True, blank=True)
    check_out_time = models.TimeField(null=True, blank=True)
    remarks = models.TextField(blank=True, null=True)
    
    def __str__(self):
        status = "Present" if self.present else "Absent"
        return f"{self.session.student} - {self.session.session_date} - {status}"
    



from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('successful', 'Successful'),
        ('failed', 'Failed'),
    )

    student_package = models.ForeignKey(
        StudentPackage, on_delete=models.CASCADE, related_name="payments"  # ✅ Changed to ForeignKey
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for {self.student_package.student.user.username} - {self.status}"


