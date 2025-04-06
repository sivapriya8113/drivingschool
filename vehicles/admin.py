from django.contrib import admin
from .models import Vehicle,VehicleAssignmentHistory,MaintenanceRecord
# Register your models here.

admin.site.register(Vehicle)
admin.site.register(VehicleAssignmentHistory)
admin.site.register(MaintenanceRecord)