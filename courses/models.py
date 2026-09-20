from django.db import models
from django.conf import settings

class Course(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    thumbnail = models.ImageField(upload_to='courses/', blank=True, null=True)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=1)
    video_url = models.URLField(blank=True, help_text="Embed link for video lesson")
    content = models.TextField(help_text="Markdown or rich text reading material")
    reflection_prompt = models.TextField(blank=True, help_text="Gentle reflection question instead of a quiz")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.course.title} - Module {self.order}: {self.title}"


class UserCourseProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='course_progress')
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'module')

    def __str__(self):
        return f"{self.user} - {self.module.title} (Completed: {self.completed})"


class PrivateJournalEntry(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='journal_entries')
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='journal_entries')
    entry_text = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'module')
        verbose_name_plural = "Private Journal Entries"

    def __str__(self):
        return f"Journal by {self.user} for {self.module.title}"
