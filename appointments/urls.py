from django.urls import path
from .views import (
    BookingView, AvailableSlotsApiView, TherapistDashboardView,
    UpdateAppointmentNotesView, CancelAppointmentView, SavePreSessionPrepApiView
)

urlpatterns = [
    path('', BookingView.as_view(), name='book_session'),
    path('api/available-slots/', AvailableSlotsApiView.as_view(), name='available_slots_api'),
    path('<int:pk>/pre-session-prep/', SavePreSessionPrepApiView.as_view(), name='save_pre_session_prep_api'),
    path('dashboard/therapist/', TherapistDashboardView.as_view(), name='therapist_dashboard'),
    path('<int:pk>/notes/', UpdateAppointmentNotesView.as_view(), name='update_appointment_notes'),
    path('<int:pk>/cancel/', CancelAppointmentView.as_view(), name='cancel_appointment'),
]
