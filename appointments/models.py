from django.db import models
from django.conf import settings

class TherapistAvailability(models.Model):
    DAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]

    therapist = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'THERAPIST'},
        related_name='availabilities'
    )
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    buffer_minutes = models.IntegerField(default=15, help_text="De-stress break time between sessions")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Therapist Availabilities"
        ordering = ['day_of_week', 'start_time']

    def __str__(self):
        day_name = dict(self.DAY_CHOICES).get(self.day_of_week, str(self.day_of_week))
        therapist_name = self.therapist.get_full_name() or self.therapist.username
        return f"{therapist_name} - {day_name} ({self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')})"


class Appointment(models.Model):
    class FocusArea(models.TextChoices):
        ANXIETY = 'ANXIETY', 'Anxiety & Stress Management'
        RELATIONSHIPS = 'RELATIONSHIPS', 'Relationships & Connection'
        PERSONAL_GROWTH = 'PERSONAL_GROWTH', 'Personal Growth & Self-Discovery'
        OTHER = 'OTHER', 'General Wellness & Other'

    class Status(models.TextChoices):
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    therapist = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'THERAPIST'},
        related_name='therapist_appointments',
        null=True,
        blank=True
    )
    focus_area = models.CharField(
        max_length=50,
        choices=FocusArea.choices,
        default=FocusArea.ANXIETY
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CONFIRMED
    )
    notes_by_client = models.TextField(blank=True, help_text="What would you like to focus on?")
    private_therapist_notes = models.TextField(blank=True, help_text="Encrypted/Private notes for therapist only")
    
    # Feature 3: Pre-Session Preparation Fields
    heaviest_emotion = models.CharField(max_length=100, blank=True, help_text="Emotion feeling heaviest before session")
    safety_preference = models.TextField(blank=True, help_text="Client note on what would make session feel safe")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date', 'start_time']

    def __str__(self):
        therapist_name = self.therapist.get_full_name() if self.therapist else "Therapist"
        return f"Appointment with {therapist_name} for {self.client} on {self.date} at {self.start_time.strftime('%H:%M')}"
