from django.contrib import admin
from .models import TherapistAvailability, Appointment

@admin.register(TherapistAvailability)
class TherapistAvailabilityAdmin(admin.ModelAdmin):
    list_display = ['therapist', 'day_of_week', 'start_time', 'end_time', 'buffer_minutes', 'is_active']
    list_filter = ['therapist', 'day_of_week', 'is_active']

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['client', 'therapist', 'focus_area', 'date', 'start_time', 'end_time', 'status', 'created_at']
    list_filter = ['therapist', 'status', 'focus_area', 'date']
    search_fields = ['client__username', 'client__email', 'therapist__first_name', 'therapist__last_name', 'notes_by_client']
