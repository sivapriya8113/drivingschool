from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Trainer
from .forms import TrainerForm, TrainerProfileForm,TrainingSessionForm
from students.models import Student
from django.utils import timezone

@login_required
def trainer_list(request):
    trainers = Trainer.objects.all()
    return render(request, 'trainers/trainer_list.html', {'trainers': trainers})

#
from django.urls import reverse

@login_required
def trainer_detail(request, trainer_id):
    # Get the trainer object, or return 404 if not found
    trainer = get_object_or_404(Trainer, id=trainer_id)

    # Query to get the assigned students, optimizing the database query with select_related
    assigned_students = StudentPackage.objects.filter(
        student__trainer=trainer  # Assuming the Student model has a 'trainer' foreign key
    ).select_related('student__user', 'package')  # Eager load related 'user' and 'package'

    # Render the template and pass the trainer and assigned_students to the context
    return render(request, 'trainers/trainer_detail.html', {
        'trainer': trainer,
        'assigned_students': assigned_students
    })

@login_required
def trainer_create(request):
    if request.method == 'POST':
        form = TrainerForm(request.POST)
        if form.is_valid():
            trainer = form.save()
            messages.success(request, 'Trainer created successfully.')
            return redirect('trainer_detail', trainer_id=trainer.id)
    else:
        form = TrainerForm()
    return render(request, 'trainers/trainer_form.html', {'form': form, 'action': 'Create'})

@login_required
def trainer_update(request, trainer_id):
    trainer = get_object_or_404(Trainer, id=trainer_id)
    if request.method == 'POST':
        form = TrainerForm(request.POST, instance=trainer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Trainer updated successfully.')
            return redirect('trainers:trainer_detail', trainer_id=trainer.id)
    else:
        form = TrainerForm(instance=trainer)
    return render(request, 'trainers/trainer_form.html', {'form': form, 'trainer': trainer, 'action': 'Update'})

@login_required
def trainer_delete(request, trainer_id):
    trainer = get_object_or_404(Trainer, id=trainer_id)
    if request.method == 'POST':
        trainer.delete()
        messages.success(request, 'Trainer deleted successfully.')
        return redirect('trainer_list')
    return render(request, 'trainers/trainer_confirm_delete.html', {'trainer': trainer})

@login_required
def trainer_schedule(request, trainer_id):
    trainer = get_object_or_404(Trainer, id=trainer_id)
    # Logic to get trainer's schedule
    # This would interact with a Schedule model that you might need to create
    return render(request, 'trainers/trainer_schedule.html', {'trainer': trainer})

@login_required
def trainer_dashboard(request):
    trainer = get_object_or_404(Trainer, user=request.user)
    assigned_students = trainer.student_set.all()
    
    # Replace this with the actual session model query
    from students.models import TrainingSession  # if your session model is named this
    upcoming_sessions = TrainingSession.objects.filter(trainer=trainer, session_date__gte=timezone.now()).order_by('session_date')

    return render(request, 'trainers/dashboard.html', {
        'trainer': trainer,
        'assigned_students': assigned_students,
        'upcoming_sessions': upcoming_sessions
    })

from students.models import StudentPackage, Payment

from django.db.models import Q

@login_required
def students_to_assign(request, trainer_id):
    trainer = get_object_or_404(Trainer, id=trainer_id)

    # Get student IDs who made payment
    paid_student_ids = Payment.objects.values_list(
        'student_package__student_id', flat=True
    ).distinct()

    # Fetch students who are:
    # - in paid list
    # - not yet assigned a trainer
    # - not staff/superuser
    unassigned_students = Student.objects.filter(
        id__in=paid_student_ids,
        trainer__isnull=True,
        user__is_staff=False,
        user__is_superuser=False
    )

    # Now filter the StudentPackages for those students
    eligible_packages = StudentPackage.objects.filter(
        student__in=unassigned_students
    ).select_related('student__user', 'package')

    return render(request, 'trainers/assign_students.html', {
        'trainer': trainer,
        'students': eligible_packages
    })


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from students.models import Student
from .forms import StudentAssignmentForm


@login_required
def assign_trainer_vehicle(request, student_id):
    student = get_object_or_404(Student, id=student_id)

    if request.method == 'POST':
        form = StudentAssignmentForm(request.POST, instance=student)
        if form.is_valid():
            assigned_student = form.save(commit=False)
            assigned_student.trainer = form.cleaned_data['trainer']
            assigned_student.vehicle = form.cleaned_data['vehicle']
            assigned_student.save()

            print("POSTED TRAINER:", form.cleaned_data['trainer'])
            print("POSTED VEHICLE:", form.cleaned_data['vehicle'])
            print(f"Assigned student {assigned_student.id} to trainer {assigned_student.trainer}")
            messages.success(request, "Trainer and vehicle assigned successfully!")
            return redirect('trainers:students_to_assign', trainer_id=assigned_student.trainer.id if assigned_student.trainer else 1)
    else:
        form = StudentAssignmentForm(instance=student)

    return render(request, 'trainers/assign_trainer_vehicle.html', {
        'form': form,
        'student': student,
    })


@login_required
def assign_training_session(request, student_id):
    student = get_object_or_404(Student, id=student_id)

    # ⛔ Prevent assigning session if trainer is not assigned
    if not student.trainer:
        messages.warning(request, "Trainer not assigned to this student yet.")
        return redirect('trainers:assign_trainer_vehicle', student_id=student.id)

    if request.method == 'POST':
        form = TrainingSessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.student = student
            session.save()
            messages.success(request, "Training session assigned successfully.")
            return redirect('trainers:students_to_assign', trainer_id=student.trainer.id)
    else:
        form = TrainingSessionForm()

    return render(request, 'trainers/assign_training_session.html', {
        'form': form,
        'student': student
    })