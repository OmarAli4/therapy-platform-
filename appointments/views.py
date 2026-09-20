import json
from datetime import datetime, timedelta, time
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import TherapistAvailability, Appointment

User = get_user_model()

class AvailableSlotsApiView(View):
    """
    Returns available 45-minute booking slots for a selected date,
    factoring in therapist availability and 15-minute buffer times.
    """
    def get(self, request, *args, **kwargs):
        date_str = request.GET.get('date')
        if not date_str:
            return JsonResponse({'error': 'Date parameter is required'}, status=400)

        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=400)

        # Do not allow booking in the past
        if target_date < timezone.now().date():
            return JsonResponse({'slots': []})

        day_of_week = target_date.weekday()  # 0=Monday, 6=Sunday

        # Fetch active availabilities
        availabilities = TherapistAvailability.objects.filter(
            day_of_week=day_of_week,
            is_active=True
        )

        # Existing confirmed appointments for that date
        existing_appointments = Appointment.objects.filter(
            date=target_date,
            status__in=[Appointment.Status.CONFIRMED, Appointment.Status.COMPLETED]
        )

        booked_intervals = []
        for appt in existing_appointments:
            booked_intervals.append((appt.start_time, appt.end_time))

        available_slots = []

        session_duration = timedelta(minutes=45)

        for avail in availabilities:
            buffer = timedelta(minutes=avail.buffer_minutes)
            slot_step = session_duration + buffer

            current_start_dt = datetime.combine(target_date, avail.start_time)
            end_dt = datetime.combine(target_date, avail.end_time)

            while current_start_dt + session_duration <= end_dt:
                slot_start_time = current_start_dt.time()
                slot_end_time = (current_start_dt + session_duration).time()

                # Check overlap with existing appointments
                is_overlap = False
                for b_start, b_end in booked_intervals:
                    if not (slot_end_time <= b_start or slot_start_time >= b_end):
                        is_overlap = True
                        break

                if not is_overlap:
                    start_str = slot_start_time.strftime('%H:%M')
                    end_str = slot_end_time.strftime('%H:%M')
                    display_str = f"{slot_start_time.strftime('%I:%M %p')} - {slot_end_time.strftime('%I:%M %p')}"
                    available_slots.append({
                        'start_time': start_str,
                        'end_time': end_str,
                        'display': display_str
                    })

                current_start_dt += slot_step

        return JsonResponse({'slots': available_slots})


class BookingView(TemplateView):
    template_name = 'appointments/booking.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['focus_areas'] = Appointment.FocusArea.choices
        context['therapist'] = User.objects.filter(role=User.Role.THERAPIST).first()
        context['min_date'] = timezone.now().strftime('%Y-%m-%d')
        return context

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Please log in or create an account to finalize your booking.")
            return redirect('login')

        focus_area = request.POST.get('focus_area')
        date_str = request.POST.get('date')
        start_time_str = request.POST.get('start_time')
        end_time_str = request.POST.get('end_time')
        notes = request.POST.get('notes_by_client', '')

        if not (focus_area and date_str and start_time_str and end_time_str):
            messages.error(request, "Please select all required session details.")
            return redirect('book_session')

        try:
            appt_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()
        except ValueError:
            messages.error(request, "Invalid date or time slot selected.")
            return redirect('book_session')

        # Double check slot availability
        existing = Appointment.objects.filter(
            date=appt_date,
            start_time=start_time,
            status=Appointment.Status.CONFIRMED
        ).exists()

        if existing:
            messages.error(request, "That time slot was just booked by another client. Please select another time.")
            return redirect('book_session')

        # Create appointment
        appointment = Appointment.objects.create(
            client=request.user,
            focus_area=focus_area,
            date=appt_date,
            start_time=start_time,
            end_time=end_time,
            status=Appointment.Status.CONFIRMED,
            notes_by_client=notes
        )

        return render(request, 'appointments/booking_confirmation.html', {'appointment': appointment})


class SavePreSessionPrepApiView(LoginRequiredMixin, View):
    """
    Feature 3: Saves pre-session reflection notes from client confirmation page.
    """
    def post(self, request, pk, *args, **kwargs):
        appointment = get_object_or_404(Appointment, pk=pk, client=request.user)
        try:
            data = json.loads(request.body)
            appointment.heaviest_emotion = data.get('heaviest_emotion', '')
            appointment.safety_preference = data.get('safety_preference', '')
            appointment.save()
            return JsonResponse({'status': 'success', 'message': 'Pre-session reflection attached to your booking!'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


class TherapistDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'appointments/therapist_dashboard.html'

    def test_func(self):
        return self.request.user.is_therapist

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()

        context['today_appointments'] = Appointment.objects.filter(
            date=today
        ).select_related('client').order_by('start_time')

        context['upcoming_appointments'] = Appointment.objects.filter(
            date__gt=today,
            status=Appointment.Status.CONFIRMED
        ).select_related('client').order_by('date', 'start_time')

        context['past_appointments'] = Appointment.objects.filter(
            date__lt=today
        ).select_related('client').order_by('-date', '-start_time')[:10]

        context['availabilities'] = TherapistAvailability.objects.filter(
            therapist=self.request.user
        ).order_by('day_of_week')

        return context


class UpdateAppointmentNotesView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_therapist

    def post(self, request, pk, *args, **kwargs):
        appointment = get_object_or_404(Appointment, pk=pk)
        private_notes = request.POST.get('private_therapist_notes', '')
        status = request.POST.get('status')

        appointment.private_therapist_notes = private_notes
        if status in [choice[0] for choice in Appointment.Status.choices]:
            appointment.status = status

        appointment.save()
        messages.success(request, f"Updated notes for session on {appointment.date}.")
        return redirect('therapist_dashboard')


class CancelAppointmentView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        appointment = get_object_or_404(Appointment, pk=pk)

        # Only client who owns it or therapist can cancel
        if request.user != appointment.client and not request.user.is_therapist:
            messages.error(request, "Permission denied.")
            return redirect('dashboard')

        appointment.status = Appointment.Status.CANCELLED
        appointment.save()
        messages.success(request, "Appointment has been cancelled.")

        if request.user.is_therapist:
            return redirect('therapist_dashboard')
        return redirect('client_dashboard')
