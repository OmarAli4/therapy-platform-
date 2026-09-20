import json
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, DetailView
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages

from .models import Course, Module, UserCourseProgress, PrivateJournalEntry

class CourseListView(ListView):
    model = Course
    template_name = 'courses/course_list.html'
    context_object_name = 'courses'

    def get_queryset(self):
        return Course.objects.filter(is_published=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            # Map progress per course
            progress_map = {}
            for course in context['courses']:
                total = course.modules.count()
                if total > 0:
                    completed = UserCourseProgress.objects.filter(
                        user=self.request.user,
                        module__course=course,
                        completed=True
                    ).count()
                    progress_map[course.id] = int((completed / total) * 100)
                else:
                    progress_map[course.id] = 0
            context['progress_map'] = progress_map
        return context


class CourseDetailView(DetailView):
    model = Course
    template_name = 'courses/course_detail.html'
    context_object_name = 'course'
    slug_field = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.object
        modules = course.modules.all()

        completed_module_ids = []
        if self.request.user.is_authenticated:
            completed_module_ids = list(
                UserCourseProgress.objects.filter(
                    user=self.request.user,
                    module__course=course,
                    completed=True
                ).values_list('module_id', flat=True)
            )

        context['modules'] = modules
        context['completed_module_ids'] = completed_module_ids
        context['total_modules'] = modules.count()
        context['completed_count'] = len(completed_module_ids)
        if modules.count() > 0:
            context['progress_percentage'] = int((len(completed_module_ids) / modules.count()) * 100)
        else:
            context['progress_percentage'] = 0

        return context


class ModuleDetailView(LoginRequiredMixin, View):
    template_name = 'courses/module_detail.html'

    def get(self, request, slug, module_id, *args, **kwargs):
        course = get_object_or_404(Course, slug=slug, is_published=True)
        module = get_object_or_404(Module, id=module_id, course=course)

        all_modules = list(course.modules.all())
        current_index = next((i for i, m in enumerate(all_modules) if m.id == module.id), 0)

        prev_module = all_modules[current_index - 1] if current_index > 0 else None
        next_module = all_modules[current_index + 1] if current_index < len(all_modules) - 1 else None

        # User progress
        progress, _ = UserCourseProgress.objects.get_or_create(
            user=request.user,
            module=module
        )

        # Private journal entry for this specific user & module ONLY
        journal_entry, _ = PrivateJournalEntry.objects.get_or_create(
            user=request.user,
            module=module,
            defaults={'entry_text': ''}
        )

        context = {
            'course': course,
            'module': module,
            'all_modules': all_modules,
            'prev_module': prev_module,
            'next_module': next_module,
            'is_completed': progress.completed,
            'journal_entry': journal_entry,
        }
        return render(request, self.template_name, context)


class SaveJournalApiView(LoginRequiredMixin, View):
    """
    Auto-saves private reflection journal entry.
    Strictly isolated: user can only modify their own journal entry.
    """
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            module_id = data.get('module_id')
            entry_text = data.get('entry_text', '')

            if not module_id:
                return JsonResponse({'status': 'error', 'message': 'Module ID missing'}, status=400)

            module = get_object_or_404(Module, id=module_id)

            journal, created = PrivateJournalEntry.objects.get_or_create(
                user=request.user,
                module=module
            )
            journal.entry_text = entry_text
            journal.save()

            return JsonResponse({
                'status': 'success',
                'message': 'Journal saved',
                'updated_at': journal.updated_at.strftime('%I:%M %p')
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


class ToggleModuleProgressApiView(LoginRequiredMixin, View):
    """
    Toggles completion status for a module.
    """
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            module_id = data.get('module_id')

            if not module_id:
                return JsonResponse({'status': 'error', 'message': 'Module ID missing'}, status=400)

            module = get_object_or_404(Module, id=module_id)

            progress, created = UserCourseProgress.objects.get_or_create(
                user=request.user,
                module=module
            )
            progress.completed = not progress.completed
            progress.save()

            return JsonResponse({
                'status': 'success',
                'completed': progress.completed
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
