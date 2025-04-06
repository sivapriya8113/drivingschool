# admins/urls.py
from django.urls import path
from . import views

app_name = 'admins'

urlpatterns = [
    path('login/', views.admin_login, name='admin_login'),
    path('logout/', views.admin_logout, name='admin_logout'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('students/', views.manage_students, name='manage_students'),
    path('trainers/', views.manage_trainers, name='manage_trainers'),
    path('vehicles/', views.manage_vehicles, name='manage_vehicles'),
    path('add-admin/', views.add_admin, name='add_admin'),
    path('assign-sessions/<int:pk>/', views.assign_sessions_view, name='assign_sessions'),
]