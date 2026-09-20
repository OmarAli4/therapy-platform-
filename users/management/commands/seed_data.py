from datetime import time
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from appointments.models import TherapistAvailability
from courses.models import Course, Module

User = get_user_model()

class Command(BaseCommand):
    help = "Seeds initial data for Sanctuary Therapy Platform (therapist, client, working hours, and sample course)."

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE("Seeding Sanctuary database..."))

        # 1. Create Therapist Dr. Wessam
        therapist, created = User.objects.get_or_create(
            username='therapist@sanctuary.com',
            defaults={
                'email': 'therapist@sanctuary.com',
                'first_name': 'Dr.',
                'last_name': 'Wessam',
                'role': User.Role.THERAPIST,
                'phone_number': '+1 (555) 234-5678',
                'bio': 'Licensed Therapist specializing in anxiety management, somatic grounding, relationship growth, and gentle life transitions. Dedicated to creating a warm, non-judgmental space for your healing journey.',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if not created:
            therapist.first_name = 'Dr.'
            therapist.last_name = 'Wessam'
            therapist.save()
            self.stdout.write(self.style.SUCCESS("Updated Therapist to Dr. Wessam"))
        else:
            therapist.set_password('password123')
            therapist.save()
            self.stdout.write(self.style.SUCCESS(f"Created Therapist: {therapist.email}"))

        # 2. Create Sample Client
        client, created = User.objects.get_or_create(
            username='client@sanctuary.com',
            defaults={
                'email': 'client@sanctuary.com',
                'first_name': 'Sarah',
                'last_name': 'Jenkins',
                'role': User.Role.CLIENT,
                'phone_number': '+1 (555) 876-5432',
                'bio': 'Seeking balance and mindful growth.'
            }
        )
        if created:
            client.set_password('password123')
            client.save()
            self.stdout.write(self.style.SUCCESS(f"Created Sample Client: {client.email}"))
        else:
            self.stdout.write(f"Client already exists: {client.email}")

        # 3. Create Therapist Availability (Mon - Fri, 09:00 to 17:00, 15m buffer)
        for day in range(0, 5):  # Monday through Friday
            avail, _ = TherapistAvailability.objects.get_or_create(
                therapist=therapist,
                day_of_week=day,
                defaults={
                    'start_time': time(9, 0),
                    'end_time': time(17, 0),
                    'buffer_minutes': 15,
                    'is_active': True
                }
            )
        self.stdout.write(self.style.SUCCESS("Set Therapist Availability (Mon-Fri 9:00 - 17:00)."))

        # 4. Create Sample Course & Modules
        course, created = Course.objects.get_or_create(
            slug='understanding-anxiety',
            defaults={
                'title': 'Understanding Anxiety & Finding Ground',
                'description': 'A gentle, self-paced exploration into somatic grounding techniques, reframing anxious thoughts, and building daily micro-rituals of tranquility.',
                'is_published': True
            }
        )

        modules_data = [
            {
                'order': 1,
                'title': 'Introduction to Somatic Grounding',
                'video_url': 'https://www.youtube.com/embed/tEmt1Znux58',
                'content': """### Welcome to Your Grounding Journey

When anxiety strikes, our sympathetic nervous system enters a state of hyper-arousal. Somatic grounding gently reminds your mind and body that you are safe in this present moment.

#### The 5-4-3-2-1 Grounding Method:
1. **5 Things You Can See:** Softly look around your space. Notice colors, light reflections, or textures.
2. **4 Things You Can Touch:** Feel the fabric of your sweater, the warmth of a mug, or the solid floor beneath your feet.
3. **3 Things You Can Hear:** Listen for distant ambient sounds, a ticking clock, or your own gentle breath.
4. **2 Things You Can Smell:** Scent of tea, fresh air, or essential oil.
5. **1 Thing You Can Taste:** A sip of water or pleasant aftertaste.

*Remember: There is no rush. Take all the time you need.*""",
                'reflection_prompt': 'Notice how your shoulders and neck feel right now. What physical sensation is your body holding onto today, and what gentle word does it need to hear?'
            },
            {
                'order': 2,
                'title': 'Navigating Intrusive Thoughts',
                'video_url': 'https://www.youtube.com/embed/inpok4MKVLM',
                'content': """### Observing Thoughts Without Judgment

Intrusive thoughts are like passing clouds in an expansive sky. You are the sky, not the clouds. 

#### Cognitive Reframing Technique:
- Instead of saying: *"I am overwhelmed and losing control."*
- Try gently reframing: *"I am noticing a feeling of overwhelm right now, and I can pause to breathe."*

By shifting from **identification** to **observation**, we create emotional space between ourselves and our anxiety.""",
                'reflection_prompt': 'What is a recurring thought that has felt heavy recently? Imagine placing it gently on a leaf floating down a calm, clear stream.'
            },
            {
                'order': 3,
                'title': 'Creating Daily Calm Rituals',
                'video_url': 'https://www.youtube.com/embed/ZToicYHKjxs',
                'content': """### Building Micro-Moments of Peace

Consistency in self-care doesn't require hours of meditation. Small, intentional 3-minute rituals throughout your day act as powerful anchors against daily stress.

#### Sample Micro-Rituals:
- **Morning Awakening:** Drinking your first cup of warm tea or water with both hands, away from screens.
- **Midday Breath Pause:** Taking 3 slow, deep belly breaths before starting a new task.
- **Evening Wind-Down:** Dimming lights 30 minutes before sleep and placing a hand on your heart.""",
                'reflection_prompt': 'Design one small 3-minute micro-ritual you can treat yourself to tomorrow morning. How can you make it feel comforting?'
            }
        ]

        for mod_info in modules_data:
            Module.objects.get_or_create(
                course=course,
                order=mod_info['order'],
                defaults={
                    'title': mod_info['title'],
                    'video_url': mod_info['video_url'],
                    'content': mod_info['content'],
                    'reflection_prompt': mod_info['reflection_prompt']
                }
            )

        self.stdout.write(self.style.SUCCESS("Created sample course and 3 grounding modules."))
        self.stdout.write(self.style.SUCCESS("Database seeding completed successfully!"))
