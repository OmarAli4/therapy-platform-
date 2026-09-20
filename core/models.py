from django.db import models
from django.conf import settings
from django.utils import timezone

class SomaticEnergyLog(models.Model):
    class EnergyLevel(models.TextChoices):
        CALM = 'CALM', '🌿 Calm'
        OVERWHELMED = 'OVERWHELMED', '🌧️ Overwhelmed'
        HOPEFUL = 'HOPEFUL', '☀️ Hopeful'
        EXHAUSTED = 'EXHAUSTED', '😴 Exhausted'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='energy_logs'
    )
    date = models.DateField(default=timezone.now)
    energy_level = models.CharField(
        max_length=20,
        choices=EnergyLevel.choices,
        default=EnergyLevel.CALM
    )
    note = models.CharField(max_length=255, blank=True, help_text="Optional short 1-line reflection note")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        unique_together = ['user', 'date']

    def __str__(self):
        return f"{self.user} - {self.get_energy_level_display()} on {self.date}"


class KindnessMessage(models.Model):
    text = models.TextField(max_length=280)
    author_alias = models.CharField(max_length=50, default="A Fellow Traveler 🌿")
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=True)
    likes_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Kindness Note by {self.author_alias}: '{self.text[:30]}...'"
