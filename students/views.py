from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Student, TrainingSession, Tutorial,StudentPackage,Payment,Trainer,Course,TrainingPackage,Vehicle
from .forms import StudentProfileForm, SessionBookingForm,PaymentForm
import uuid 
from django.http import HttpResponse
from django.conf import settings
from django.http import JsonResponse
import razorpay
from django.views.decorators.csrf import csrf_exempt
import json
import logging
from datetime import timedelta, date
from django.utils import timezone


@login_required
def dashboard(request):
    """Student dashboard showing upcoming sessions and available tutorials"""
    try:
        student = Student.objects.get(user=request.user)
        bookings = StudentPackage.objects.filter(student=student)
        # 🔥 Only fetch future sessions
        upcoming_sessions = TrainingSession.objects.filter(
            student=student,
            session_date__gte=timezone.now().date(),
            completed=False
        ).order_by('session_date', 'time_slot')
        print("iiiiii",upcoming_sessions)
    except Student.DoesNotExist:
        # If the student profile doesn't exist yet, create one
        student = Student.objects.create(
            user=request.user,
            address="",
            phone_number="",
            student_type="local"
        )
        upcoming_sessions = []
    
    tutorials = Tutorial.objects.filter(visible=True)
    
    context = {
        'student': student,
        'upcoming_sessions': upcoming_sessions,
        'tutorials': tutorials,
        'bookings':bookings
    }
    return render(request, 'students/dashboard.html', context)


@login_required
def profile(request):
    """View and update student profile"""
    student = get_object_or_404(Student, user=request.user)
    
    if request.method == 'POST':
        form = StudentProfileForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('students:profile')
    else:
        form = StudentProfileForm(instance=student)
    bookings = StudentPackage.objects.filter(student=student.id)
    return render(request, 'students/profile.html', {'form': form,'book':bookings})


# in students/views.py
from django.contrib.admin.views.decorators import staff_member_required

@login_required
def student_detail(request, pk):
    student = get_object_or_404(Student, pk=pk)
    return render(request, 'students/student_detail.html', {'student': student})

def available_courses(request):
    print("🔍 DEBUG: available_courses view is executing...")
    
    courses = Course.objects.prefetch_related('packages').all()
    
    print(f"📢 Found {courses.count()} courses")
    for course in courses:
        print(f"✅ Course: {course.title}, Packages: {list(course.packages.all())}")
    
    return render(request, "students/courses.html", {"courses": courses}) # Temporary response for testing


import re

def convert_to_embed(url):
    # Match different YouTube URL patterns
    patterns = [
        r"(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=([\w-]+)",  # Standard YouTube link
        r"(?:https?:\/\/)?youtu\.be\/([\w-]+)",                        # Shortened youtu.be link
        r"(?:https?:\/\/)?(?:www\.)?youtube\.com\/embed\/([\w-]+)"    # Already an embed link
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            video_id = match.group(1)
            return f"https://www.youtube.com/embed/{video_id}"

    return url  # Return original URL if no match is found


@login_required
def view_tutorial(request, tutorial_id):
    tutorial = get_object_or_404(Tutorial, id=tutorial_id, visible=True)

    # Ensure the video URL is converted
    tutorial.video_url = convert_to_embed(tutorial.video_url)

    # Debug the converted URL
    print("Converted URL:", tutorial.video_url)

    return render(request, 'students/tutorial_detail.html', {'tutorial': tutorial})

@login_required
def session_history(request):
    """View past training sessions"""
    student = get_object_or_404(Student, user=request.user)
    completed_sessions = TrainingSession.objects.filter(
        student=student, completed=True
    ).order_by('-session_date', '-time_slot')
    
    return render(request, 'students/session_history.html', {'sessions': completed_sessions})


@login_required
def tutorial_list(request):
    """View all available tutorials"""
    tutorials = Tutorial.objects.filter(visible=True).order_by('-updated_at')
    return render(request, 'students/tutorial_list.html', {'tutorials': tutorials})


logger = logging.getLogger(__name__)

# Initialize Razorpay Client
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

@csrf_exempt
@login_required
def initiate_payment(request):
    if request.method == "POST":
        print("ss",request.user.id)
        try:
            data = json.loads(request.body)
            package_id = data.get("package")

            student = Student.objects.get(user=request.user)

            if not package_id:
                return JsonResponse({"error": "Missing package ID"}, status=400)

            package = get_object_or_404(TrainingPackage, id=package_id)

            # ✅ Prevent duplicate purchases
            if StudentPackage.objects.filter(student=student, package=package, payment_status=True).exists():
                return JsonResponse({"error": "You have already purchased this package."}, status=400)

            # ✅ Create a new StudentPackage if not exists or in progress
            student_package, created = StudentPackage.objects.get_or_create(
                student=student,
                package=package,
                defaults={"payment_status": False, "remaining_sessions": package.sessions}
            )

            # ✅ Avoid duplicate payment initiation
            existing_payment = Payment.objects.filter(
                student_package=student_package,
                status="pending"
            ).first()

            if existing_payment:
                return JsonResponse({
                    "order_id": existing_payment.razorpay_order_id,
                    "amount": int(package.price * 100),
                    "currency": "INR",
                    "razorpay_key": settings.RAZORPAY_KEY_ID,
                    "package_id": package_id
                })

            # ✅ Create Razorpay order
            order_data = {
                "amount": int(package.price * 100),
                "currency": "INR",
                "payment_capture": "1",
            }
            order = razorpay_client.order.create(data=order_data)

            # ✅ Save payment object
            payment = Payment.objects.create(
                student_package=student_package,
                amount=package.price,
                razorpay_order_id=order["id"],
                status="pending",
            )

            return JsonResponse({
                "order_id": payment.razorpay_order_id,
                "amount": order_data["amount"],
                "currency": order_data["currency"],
                "razorpay_key": settings.RAZORPAY_KEY_ID,
                "package_id": package_id
            })

        except Exception as e:
            logger.error(f"Error in initiate_payment: {e}")
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Invalid request"}, status=400)


@csrf_exempt
def verify_payment(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            razorpay_order_id = data.get("razorpay_order_id")
            razorpay_payment_id = data.get("razorpay_payment_id")
            razorpay_signature = data.get("razorpay_signature")

            payment = get_object_or_404(Payment, razorpay_order_id=razorpay_order_id)

            # Verify Razorpay Signature
            params_dict = {
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature
            }

            result = razorpay_client.utility.verify_payment_signature(params_dict)
            if result:
                # ✅ Update payment details
                payment.status = "successful"
                payment.razorpay_payment_id = razorpay_payment_id
                payment.razorpay_signature = razorpay_signature
                payment.save()

                # ✅ Mark student package as paid
                student_package = payment.student_package
                student_package.payment_status = True
                student_package.save()

                # ✅ Auto-assign sessions
                # Auto-assign sessions here
                assign_sessions(payment.student_package)

                return JsonResponse({"status": "success"})
            else:
                payment.status = "failed"
                payment.save()
                return JsonResponse({"status": "failure"}, status=400)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Invalid request"}, status=400)


def assign_sessions(student_package):
    student = student_package.student
    sessions_to_create = student_package.package.sessions
    trainer = student.trainer  # Use assigned trainer
    vehicle = Vehicle.objects.filter(vehicle_type=student_package.package.vehicle_type, is_active=True).first()
    
    if not trainer or not vehicle:
        print("❌ Trainer or vehicle not available!")
        return  # Or handle this better

    start_date = date.today() + timedelta(days=1)  # start from tomorrow
    time_slots = [slot[0] for slot in TrainingSession.TIME_SLOTS]
    created = 0

    while created < sessions_to_create:
        for time_slot in time_slots:
            if created >= sessions_to_create:
                break
            # Check if trainer already has a session in this slot
            exists = TrainingSession.objects.filter(
                trainer=trainer,
                session_date=start_date,
                time_slot=time_slot
            ).exists()
            if not exists:
                TrainingSession.objects.create(
                    student=student,
                    trainer=trainer,
                    vehicle=vehicle,
                    student_package=student_package,
                    session_date=start_date,
                    time_slot=time_slot
                )
                created += 1
        start_date += timedelta(days=1)