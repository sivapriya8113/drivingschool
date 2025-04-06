# admins/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import AdminRegistrationForm, AdminLoginForm
from .models import Admin
from students.models import Student
from trainers.models import Trainer
from vehicles.models import Vehicle

def admin_login(request):
    if request.method == 'POST':
        form = AdminLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None and hasattr(user, 'admin'):
                login(request, user)
                return redirect('admins:admin_dashboard')  # ✅ Correct
            else:
                messages.error(request, 'Invalid admin credentials')
    else:
        form = AdminLoginForm()
    return render(request, 'admins/login.html', {'form': form})

@login_required
def admin_logout(request):
    logout(request)
    return redirect('admins:admin_login')

@login_required
def admin_dashboard(request):
    if not hasattr(request.user, 'admin'):
        messages.error(request, "You are not authorized to access the admin dashboard.")
        return redirect('accounts:home')  # redirect to home or login

    student_count = Student.objects.count()
    trainer_count = Trainer.objects.count()
    vehicle_count = Vehicle.objects.count()

    context = {
        'student_count': student_count,
        'trainer_count': trainer_count,
        'vehicle_count': vehicle_count,
    }
    return render(request, 'admins/dashboard.html', context)

@login_required
def manage_students(request):
    if not hasattr(request.user, 'admin'):
        return redirect('home')
        
    students = Student.objects.all()
    return render(request, 'admins/manage_students.html', {'students': students})

@login_required
def manage_trainers(request):
    if not hasattr(request.user, 'admin'):
        return redirect('home')
        
    trainers = Trainer.objects.all()
    return render(request, 'admins/manage_trainers.html', {'trainers': trainers})

@login_required
def manage_vehicles(request):
    if not hasattr(request.user, 'admin'):
        return redirect('home')
        
    vehicles = Vehicle.objects.all()
    return render(request, 'admins/manage_vehicles.html', {'vehicles': vehicles})

@login_required
def add_admin(request):
    # Only primary admin can add another admin
    if not hasattr(request.user, 'admin') or not request.user.admin.is_primary:
        return redirect('admins:admin_dashboard')
        
    if request.method == 'POST':
        form = AdminRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            Admin.objects.create(
                user=user,
                phone=form.cleaned_data['phone'],
                address=form.cleaned_data['address'],
                is_primary=form.cleaned_data['is_primary']
            )
            messages.success(request, 'New admin created successfully')
            return redirect('admins:admin_dashboard')  # ✅
    else:
        form = AdminRegistrationForm()
    return render(request, 'admins/add_admin.html', {'form': form})

# 🚀 Admin-triggered session assignment view
from students.models import StudentPackage
from students.utils import assign_sessions  # import your session assigning logic

@login_required
def assign_sessions_view(request, pk):
    if not hasattr(request.user, 'admin'):
        messages.error(request, "🚫 You are not authorized to assign sessions.")
        return redirect('admins:admin_dashboard')

    package = get_object_or_404(StudentPackage, pk=pk)

    if not package.payment_status:
        messages.warning(request, "⏳ Payment not completed. Cannot assign sessions.")
    else:
        try:
            assign_sessions(package)
            messages.success(request, f"✅ Sessions successfully assigned for {package.student}")
        except Exception as e:
            messages.error(request, f"❌ Error while assigning sessions: {e}")

    return redirect('admins:manage_students')  # or wherever you're managing student packages