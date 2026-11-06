import json
from datetime import datetime, timedelta
from django.shortcuts import render, redirect
from django.views import View
from django.views.generic import TemplateView, CreateView
from django.contrib.auth import login, get_user_model
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone

from appointments.models import Appointment
from courses.models import Course, UserCourseProgress, PrivateJournalEntry
from core.forms import ClientRegistrationForm
from core.models import SomaticEnergyLog, KindnessMessage

User = get_user_model()

def get_weekly_energy_chart(user):
    today = timezone.now().date()
    start_date = today - timedelta(days=6)
    
    logs = SomaticEnergyLog.objects.filter(
        user=user,
        date__range=[start_date, today]
    )
    logs_by_date = {log.date: log for log in logs}

    chart_data = []
    energy_meta = {
        'HOPEFUL': {'emoji': '☀️', 'label': 'Hopeful', 'height': 85, 'bg': 'bg-[#D4A55A]', 'text': 'text-[#D4A55A]'},
        'CALM': {'emoji': '🌿', 'label': 'Calm', 'height': 70, 'bg': 'bg-[#2D6B52]', 'text': 'text-[#6BAF8A]'},
        'OVERWHELMED': {'emoji': '🌧️', 'label': 'Overwhelmed', 'height': 45, 'bg': 'bg-[#3A7361]', 'text': 'text-[#3A7361]'},
        'EXHAUSTED': {'emoji': '😴', 'label': 'Exhausted', 'height': 30, 'bg': 'bg-[#344A40]', 'text': 'text-[#8A9EA8]'},
    }

    for i in range(7):
        current_date = start_date + timedelta(days=i)
        day_log = logs_by_date.get(current_date)

        if day_log:
            level = day_log.energy_level
            meta = energy_meta.get(level, energy_meta['CALM'])
            chart_data.append({
                'day_name': current_date.strftime('%a'),
                'date_str': current_date.strftime('%Y-%m-%d'),
                'is_today': current_date == today,
                'logged': True,
                'level': level,
                'emoji': meta['emoji'],
                'label': meta['label'],
                'height': meta['height'],
                'bg_class': meta['bg'],
                'text_class': meta['text'],
                'note': day_log.note
            })
        else:
            chart_data.append({
                'day_name': current_date.strftime('%a'),
                'date_str': current_date.strftime('%Y-%m-%d'),
                'is_today': current_date == today,
                'logged': False,
                'level': '',
                'emoji': '⚪',
                'label': 'Unlogged',
                'height': 15,
                'bg_class': 'bg-[#1A2420]',
                'text_class': 'text-[#8A9EA8]',
                'note': ''
            })

    return chart_data


class LandingView(TemplateView):
    template_name = 'core/landing.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['courses'] = Course.objects.filter(is_published=True)[:3]
        therapists = User.objects.filter(role=User.Role.THERAPIST, is_active=True).prefetch_related('availabilities').order_by('id')
        context['therapists'] = therapists
        context['therapist'] = therapists.first()
        return context


class CalmSpaceView(TemplateView):
    """
    Feature 5: Passwordless, no-account-needed calming room accessible to anyone.
    Includes Feature 4: Wall of Gentle Kindness.
    """
    template_name = 'core/calm_space.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['courses'] = Course.objects.filter(is_published=True)[:2]
        context['kindness_messages'] = KindnessMessage.objects.filter(is_approved=True).order_by('-created_at')[:8]
        return context


class RegisterView(CreateView):
    form_class = ClientRegistrationForm
    template_name = 'core/register.html'
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, "Welcome to KindSoul. We are so glad you are here.")
        return redirect(self.success_url)


class CustomLoginView(LoginView):
    template_name = 'core/login.html'

    def form_valid(self, form):
        messages.success(self.request, "Welcome back. Take a deep breath—you are in a safe space.")
        return super().form_valid(form)


class DashboardRouterView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        if request.user.is_therapist:
            return redirect('therapist_dashboard')
        return redirect('client_dashboard')


class LogSomaticEnergyApiView(LoginRequiredMixin, View):
    """
    Somatic Energy Tracker API Endpoint: Logs or updates daily energy.
    """
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            energy_level = data.get('energy_level')
            note = data.get('note', '')

            if energy_level not in [choice[0] for choice in SomaticEnergyLog.EnergyLevel.choices]:
                return JsonResponse({'status': 'error', 'message': 'Invalid energy level'}, status=400)

            today = timezone.now().date()
            log, created = SomaticEnergyLog.objects.get_or_create(
                user=request.user,
                date=today,
                defaults={'energy_level': energy_level, 'note': note}
            )

            if not created:
                log.energy_level = energy_level
                if note:
                    log.note = note
                log.save()

            chart_data = get_weekly_energy_chart(request.user)
            return JsonResponse({
                'status': 'success',
                'message': 'Energy logged gently for today!',
                'chart_data': chart_data
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


class PostKindnessMessageApiView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            text = data.get('text', '').strip()
            alias = data.get('author_alias', '').strip() or 'A Fellow Traveler 🌿'

            if not text:
                return JsonResponse({'status': 'error', 'message': 'Message cannot be empty'}, status=400)

            msg = KindnessMessage.objects.create(
                text=text[:280],
                author_alias=alias[:50],
                is_approved=True
            )

            messages_list = list(KindnessMessage.objects.filter(is_approved=True).order_by('-created_at')[:8].values('id', 'text', 'author_alias', 'likes_count'))
            return JsonResponse({
                'status': 'success',
                'message': 'Your note of kindness has been posted to the wall 💌',
                'messages': messages_list
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


class LikeKindnessMessageApiView(View):
    def post(self, request, pk, *args, **kwargs):
        try:
            msg = KindnessMessage.objects.get(pk=pk)
            msg.likes_count += 1
            msg.save()
            return JsonResponse({'status': 'success', 'likes_count': msg.likes_count})
        except KindnessMessage.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Message not found'}, status=404)


class ClientDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'core/client_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # User's appointments
        context['upcoming_appointments'] = Appointment.objects.filter(
            client=user, 
            status=Appointment.Status.CONFIRMED
        ).select_related('therapist').order_by('date', 'start_time')
        
        context['past_appointments'] = Appointment.objects.filter(
            client=user
        ).exclude(status=Appointment.Status.CONFIRMED).select_related('therapist').order_by('-date', '-start_time')

        # Courses & progress
        courses = Course.objects.filter(is_published=True)
        course_data = []
        for course in courses:
            total_modules = course.modules.count()
            if total_modules > 0:
                completed_count = UserCourseProgress.objects.filter(
                    user=user, 
                    module__course=course, 
                    completed=True
                ).count()
                progress_percent = int((completed_count / total_modules) * 100)
            else:
                completed_count = 0
                progress_percent = 0

            course_data.append({
                'course': course,
                'total_modules': total_modules,
                'completed_count': completed_count,
                'progress_percent': progress_percent
            })
        
        context['course_data'] = course_data

        # Private journals
        context['journal_entries'] = PrivateJournalEntry.objects.filter(
            user=user
        ).select_related('module', 'module__course').order_by('-updated_at')

        # Somatic Energy Weekly Chart
        context['weekly_chart'] = json.dumps(get_weekly_energy_chart(user))

        # Today's log if present
        today_log = SomaticEnergyLog.objects.filter(user=user, date=timezone.now().date()).first()
        context['today_energy_level'] = today_log.energy_level if today_log else ''

        return context
