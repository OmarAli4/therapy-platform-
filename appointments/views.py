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
    Returns available 45-minute booking slots for a selected date and specific therapist,
    factoring in that therapist's availability and 15-minute buffer times.
    """
    def get(self, request, *args, **kwargs):
        date_str = request.GET.get('date')
        therapist_id = request.GET.get('therapist_id')

        if not date_str:
            return JsonResponse({'error': 'Date parameter is required'}, status=400)

        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=400)

        # Do not allow booking in the past
        if target_date < timezone.now().date():
            return JsonResponse({'slots': []})

        # Resolve selected therapist (or fallback to first active therapist)
        therapist = None
        if therapist_id:
            therapist = User.objects.filter(pk=therapist_id, role=User.Role.THERAPIST, is_active=True).first()
        if not therapist:
            therapist = User.objects.filter(role=User.Role.THERAPIST, is_active=True).first()
        if not therapist:
            return JsonResponse({'slots': []})

        day_of_week = target_date.weekday()  # 0=Monday, 6=Sunday

        # Fetch active availabilities for THIS therapist
        availabilities = TherapistAvailability.objects.filter(
            therapist=therapist,
            day_of_week=day_of_week,
            is_active=True
        )

        # Existing confirmed/completed appointments for THIS therapist on that date
        existing_appointments = Appointment.objects.filter(
            therapist=therapist,
            date=target_date,
            status__in=[Appointment.Status.CONFIRMED, Appointment.Status.COMPLETED]
        )

        booked_intervals = [(appt.start_time, appt.end_time) for appt in existing_appointments]
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

        return JsonResponse({
            'therapist_id': therapist.id,
            'therapist_name': therapist.get_full_name() or therapist.username,
            'slots': available_slots
        })


class BookingView(TemplateView):
    template_name = 'appointments/booking.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        therapists = User.objects.filter(role=User.Role.THERAPIST, is_active=True).prefetch_related('availabilities').order_by('id')
        
        requested_therapist_id = self.request.GET.get('therapist')
        selected_therapist = None
        if requested_therapist_id and requested_therapist_id.isdigit():
            selected_therapist = therapists.filter(pk=int(requested_therapist_id)).first()
        if not selected_therapist:
            selected_therapist = therapists.first()

        therapists_data = []
        day_abbr = {0: 'Mon', 1: 'Tue', 2: 'Wed', 3: 'Thu', 4: 'Fri', 5: 'Sat', 6: 'Sun'}
        for doc in therapists:
            active_days = [day_abbr.get(a.day_of_week, '') for a in doc.availabilities.all() if a.is_active]
            therapists_data.append({
                'id': doc.id,
                'name': doc.get_full_name() or doc.username,
                'specialty': doc.specialty or 'Licensed Mindful Therapist',
                'bio': doc.bio or 'Dedicated to creating a warm, non-judgmental space for your healing journey.',
                'days_summary': ', '.join(active_days) if active_days else 'Schedule by request',
            })

        context['focus_areas'] = Appointment.FocusArea.choices
        context['therapists'] = therapists
        context['therapists_json'] = json.dumps(therapists_data)
        context['selected_therapist_id'] = selected_therapist.id if selected_therapist else ''
        context['therapist'] = selected_therapist
        context['min_date'] = timezone.now().strftime('%Y-%m-%d')
        return context

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Please log in or create an account to finalize your booking.")
            return redirect('login')

        therapist_id = request.POST.get('therapist_id')
        focus_area = request.POST.get('focus_area')
        date_str = request.POST.get('date')
        start_time_str = request.POST.get('start_time')
        end_time_str = request.POST.get('end_time')
        notes = request.POST.get('notes_by_client', '')

        if not (therapist_id and focus_area and date_str and start_time_str and end_time_str):
            messages.error(request, "Please select your therapist, focus area, date, and time slot.")
            return redirect('book_session')

        therapist = get_object_or_404(User, pk=therapist_id, role=User.Role.THERAPIST, is_active=True)

        try:
            appt_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()
        except ValueError:
            messages.error(request, "Invalid date or time slot selected.")
            return redirect('book_session')

        # Double check slot availability for this specific therapist
        existing = Appointment.objects.filter(
            therapist=therapist,
            date=appt_date,
            start_time=start_time,
            status=Appointment.Status.CONFIRMED
        ).exists()

        if existing:
            messages.error(request, f"That time slot with {therapist.get_full_name()} was just booked. Please select another time.")
            return redirect('book_session')

        appointment = Appointment.objects.create(
            client=request.user,
            therapist=therapist,
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
        therapist = self.request.user

        # Filter appointments strictly for the logged-in therapist
        context['today_appointments'] = Appointment.objects.filter(
            therapist=therapist,
            date=today
        ).select_related('client').order_by('start_time')

        context['upcoming_appointments'] = Appointment.objects.filter(
            therapist=therapist,
            date__gt=today,
            status=Appointment.Status.CONFIRMED
        ).select_related('client').order_by('date', 'start_time')

        context['past_appointments'] = Appointment.objects.filter(
            therapist=therapist,
            date__lt=today
        ).select_related('client').order_by('-date', '-start_time')[:20]

        existing_avails = {
            a.day_of_week: a for a in TherapistAvailability.objects.filter(therapist=therapist)
        }

        weekly_schedule = []
        for day_num, day_label in TherapistAvailability.DAY_CHOICES:
            avail = existing_avails.get(day_num)
            weekly_schedule.append({
                'day_num': day_num,
                'day_label': day_label,
                'is_active': avail.is_active if avail else False,
                'start_time': avail.start_time.strftime('%H:%M') if avail else '09:00',
                'end_time': avail.end_time.strftime('%H:%M') if avail else '17:00',
                'buffer_minutes': avail.buffer_minutes if avail else 15,
            })

        context['weekly_schedule'] = weekly_schedule
        context['availabilities'] = TherapistAvailability.objects.filter(
            therapist=therapist,
            is_active=True
        ).order_by('day_of_week')

        return context


class UpdateTherapistAvailabilityView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Allows each logged-in therapist to manage their own weekly working hours,
    active days, and buffer minutes directly from the Therapist Dashboard.
    """
    def test_func(self):
        return self.request.user.is_therapist

    def post(self, request, *args, **kwargs):
        therapist = request.user
        for day_num, _ in TherapistAvailability.DAY_CHOICES:
            is_active = request.POST.get(f'is_active_{day_num}') == 'on'
            start_str = request.POST.get(f'start_time_{day_num}', '09:00')
            end_str = request.POST.get(f'end_time_{day_num}', '17:00')
            buffer_str = request.POST.get(f'buffer_{day_num}', '15')

            try:
                start_t = datetime.strptime(start_str, '%H:%M').time()
                end_t = datetime.strptime(end_str, '%H:%M').time()
                buffer_m = max(0, min(60, int(buffer_str)))
            except ValueError:
                continue

            if start_t >= end_t:
                continue

            TherapistAvailability.objects.update_or_create(
                therapist=therapist,
                day_of_week=day_num,
                defaults={
                    'is_active': is_active,
                    'start_time': start_t,
                    'end_time': end_t,
                    'buffer_minutes': buffer_m,
                }
            )

        messages.success(request, "Your weekly working hours and availability have been updated.")
        return redirect('therapist_dashboard')


class UpdateAppointmentNotesView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_therapist

    def post(self, request, pk, *args, **kwargs):
        appointment = get_object_or_404(Appointment, pk=pk, therapist=request.user)
        private_notes = request.POST.get('private_therapist_notes', '')
        status = request.POST.get('status')

        appointment.private_therapist_notes = private_notes
        if status in [choice[0] for choice in Appointment.Status.choices]:
            appointment.status = status

        appointment.save()
        messages.success(request, f"Updated notes for session with {appointment.client.get_full_name() or appointment.client.username} on {appointment.date}.")
        return redirect('therapist_dashboard')


class CancelAppointmentView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        appointment = get_object_or_404(Appointment, pk=pk)

        is_assigned_therapist = request.user.is_therapist and (appointment.therapist == request.user or appointment.therapist is None)
        if request.user != appointment.client and not is_assigned_therapist:
            messages.error(request, "Permission denied.")
            return redirect('dashboard')

        appointment.status = Appointment.Status.CANCELLED
        appointment.save()
        messages.success(request, "Appointment has been cancelled.")

        if request.user.is_therapist:
            return redirect('therapist_dashboard')
        return redirect('client_dashboard')
