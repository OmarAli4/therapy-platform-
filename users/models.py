from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Role(models.TextChoices):
        THERAPIST = 'THERAPIST', 'Therapist'
        CLIENT = 'CLIENT', 'Client'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CLIENT
    )
    specialty = models.CharField(
        max_length=150,
        blank=True,
        default='Licensed Mindful Therapist',
        help_text='Clinical specialty shown to clients when booking'
    )
    phone_number = models.CharField(max_length=20, blank=True)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    @property
    def is_therapist(self):
        return self.role == self.Role.THERAPIST

    @property
    def is_client(self):
        return self.role == self.Role.CLIENT

    def __str__(self):
        full_name = self.get_full_name()
        return f"{full_name} ({self.get_role_display()})" if full_name else f"{self.username} ({self.get_role_display()})"
