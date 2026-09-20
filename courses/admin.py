from django.contrib import admin
from .models import Course, Module, UserCourseProgress, PrivateJournalEntry

class ModuleInline(admin.StackedInline):
    model = Module
    extra = 1

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'is_published', 'created_at']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ModuleInline]

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'order']
    list_filter = ['course']

@admin.register(UserCourseProgress)
class UserCourseProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'module', 'completed', 'completed_at']
    list_filter = ['completed']

@admin.register(PrivateJournalEntry)
class PrivateJournalEntryAdmin(admin.ModelAdmin):
    list_display = ['user', 'module', 'updated_at']
