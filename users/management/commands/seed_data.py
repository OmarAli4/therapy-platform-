from datetime import time
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from appointments.models import TherapistAvailability, Appointment
from courses.models import Course, Module

User = get_user_model()

class Command(BaseCommand):
    help = "Seeds initial data for KindSoul Therapy Platform (multi-therapist team, client, working hours, and courses)."

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE("Seeding KindSoul database..."))

        # 1. Seed Multi-Therapist Care Team (Easy to add more doctors in the future!)
        therapists_catalog = [
            {
                'username': 'therapist@sanctuary.com',
                'email': 'therapist@sanctuary.com',
                'first_name': 'Dr.',
                'last_name': 'Wessam',
                'specialty': 'Clinical Psychologist • Anxiety, Somatic Grounding & EQ',
                'phone_number': '+1 (555) 234-5678',
                'bio': 'Specializing in anxiety relief, somatic nervous system regulation, and Emotional Intelligence (RULER). Dedicated to holding a warm, unhurried space where you feel deeply heard.',
                'is_superuser': True,
                'days': [0, 1, 2, 3, 4],  # Mon - Fri
                'start_time': time(9, 0),
                'end_time': time(17, 0),
            },
            {
                'username': 'layla@sanctuary.com',
                'email': 'layla@sanctuary.com',
                'first_name': 'Dr. Layla',
                'last_name': 'Mansour',
                'specialty': 'Relationships, Attachment & Emotionally Focused Therapy',
                'phone_number': '+1 (555) 345-6789',
                'bio': 'Helping individuals and couples heal attachment wounds, build empathetic boundaries, and cultivate safe, authentic emotional connection.',
                'is_superuser': False,
                'days': [6, 0, 1, 2, 3],  # Sun - Thu
                'start_time': time(10, 0),
                'end_time': time(18, 0),
            },
            {
                'username': 'karim@sanctuary.com',
                'email': 'karim@sanctuary.com',
                'first_name': 'Dr. Karim',
                'last_name': 'Nabil',
                'specialty': 'Burnout Recovery, ACT & Mindful Self-Compassion',
                'phone_number': '+1 (555) 456-7890',
                'bio': 'Guiding high-empathy professionals and perfectionists through burnout recovery, cognitive defusion (ACT), and Dr. Kristin Neff’s self-compassion practices.',
                'is_superuser': False,
                'days': [0, 2, 3, 5],  # Mon, Wed, Thu, Sat
                'start_time': time(11, 0),
                'end_time': time(19, 0),
            },
        ]

        primary_therapist = None
        for idx, t_info in enumerate(therapists_catalog):
            doc, created = User.objects.update_or_create(
                username=t_info['username'],
                defaults={
                    'email': t_info['email'],
                    'first_name': t_info['first_name'],
                    'last_name': t_info['last_name'],
                    'role': User.Role.THERAPIST,
                    'specialty': t_info['specialty'],
                    'phone_number': t_info['phone_number'],
                    'bio': t_info['bio'],
                    'is_staff': True,
                    'is_superuser': t_info['is_superuser'],
                    'is_active': True,
                }
            )
            if created:
                doc.set_password('password123')
                doc.save()

            if idx == 0:
                primary_therapist = doc

            for day in t_info['days']:
                TherapistAvailability.objects.update_or_create(
                    therapist=doc,
                    day_of_week=day,
                    defaults={
                        'start_time': t_info['start_time'],
                        'end_time': t_info['end_time'],
                        'buffer_minutes': 15,
                        'is_active': True
                    }
                )

        # Backfill any existing appointments without a therapist to Dr. Wessam
        if primary_therapist:
            Appointment.objects.filter(therapist__isnull=True).update(therapist=primary_therapist)

        self.stdout.write(self.style.SUCCESS("Seeded 3 KindSoul Therapists (Dr. Wessam, Dr. Layla Mansour, Dr. Karim Nabil) with custom weekly schedules."))

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

        # 4. Create Evidence-Based Courses & Modules Catalog (Easy to expand in the future!)
        courses_catalog = [
            {
                'slug': 'understanding-anxiety',
                'title': 'Understanding Anxiety & Finding Ground',
                'description': 'A gentle, self-paced exploration into somatic grounding techniques, reframing anxious thoughts, and building daily micro-rituals of tranquility.',
                'modules': [
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
            },
            {
                'slug': 'emotional-intelligence-eq-ruler',
                'title': 'Emotional Intelligence (EQ) & Naming Your Inner World',
                'description': 'Inspired by Yale’s RULER framework and Dr. Daniel Goleman’s EQ research: learn how emotional granularity calms the amygdala and transforms how you understand yourself.',
                'modules': [
                    {
                        'order': 1,
                        'title': 'The Neuroscience of "Name It to Tame It"',
                        'video_url': 'https://www.youtube.com/embed/tEmt1Znux58',
                        'content': """### Why Precise Emotion Words Heal

Neuroscientist Dr. Matthew Lieberman (UCLA) discovered through fMRI brain imaging that **Affect Labeling**—putting accurate words to our feelings—activates the right ventrolateral prefrontal cortex and reduces electrical activity in the amygdala.

#### The Yale RULER Skills:
1. **Recognizing:** Noticing shifts in your energy and physical body.
2. **Understanding:** Asking gently *"What unmet need is underneath this feeling?"*
3. **Labeling:** Moving from vague labels (*"fine"*, *"stressed"*) to granular shades (*"overstimulated"*, *"quietly hopeful"*).
4. **Expressing & Regulating:** Choosing a wise, compassionate response rather than an impulsive reaction.""",
                        'reflection_prompt': 'Think of a moment this week when you said "I am just stressed." Looking deeper, what were the 2 or 3 more specific emotions hiding underneath that word?'
                    },
                    {
                        'order': 2,
                        'title': 'Decoding Emotional Triggers with Curiosity',
                        'video_url': 'https://www.youtube.com/embed/inpok4MKVLM',
                        'content': """### Every Emotion Is a Messenger

In Emotional Intelligence, there are no "bad" emotions—even anger, envy, and grief carry sacred information about what we value most.

- **Anger / Frustration** often signals that a boundary or fairness value has been crossed.
- **Sadness / Grief** honors the depth of what we love and cherish.
- **Anxiety** highlights uncertainty around something that matters deeply to us.""",
                        'reflection_prompt': 'What emotion have you been trying to push away lately? If that emotion were a gentle messenger knocking at your door, what is it trying to protect for you?'
                    }
                ]
            },
            {
                'slug': 'self-compassion-and-deep-empathy',
                'title': 'The Art of Self-Compassion & Deep Empathy',
                'description': 'Grounded in Dr. Kristin Neff’s empirical research and Carl Rogers’ humanistic psychology: quiet your harsh inner critic and build safe, empathetic boundaries.',
                'modules': [
                    {
                        'order': 1,
                        'title': 'The Three Pillars of Self-Compassion',
                        'video_url': 'https://www.youtube.com/embed/ZToicYHKjxs',
                        'content': """### Returning Home to Yourself as a Friend

Dr. Kristin Neff’s research demonstrates that self-compassion is far more effective for emotional resilience than harsh self-criticism.

#### The 3 Core Pillars:
1. **Self-Kindness vs. Self-Judgment:** Offering yourself warmth and understanding when you suffer, fail, or feel inadequate.
2. **Common Humanity vs. Isolation:** Recognizing that suffering and personal imperfection are part of the shared human experience—not something happening to "you alone."
3. **Mindfulness vs. Over-Identification:** Holding painful thoughts and feelings in balanced awareness rather than suppressing or exaggerating them.""",
                        'reflection_prompt': 'Write down how you would speak to a dear friend going through your exact current struggle. Now read those exact words back to yourself.'
                    },
                    {
                        'order': 2,
                        'title': 'Compassionate Empathy Without Burnout',
                        'video_url': 'https://www.youtube.com/embed/tEmt1Znux58',
                        'content': """### Cognitive, Emotional, and Compassionate Empathy

Psychologists distinguish between three forms of empathy:
- **Cognitive Empathy:** Understanding another person’s perspective intellectually.
- **Emotional Empathy:** Feeling what another person feels (which alone can lead to empathetic distress if unbounded).
- **Compassionate Empathy (Empathic Concern):** Feeling warmth and care for another while staying grounded in your own nervous system.""",
                        'reflection_prompt': 'Where in your life do you absorb other people’s stress as your own? How can you care deeply while keeping your feet firmly rooted on your own ground?'
                    }
                ]
            }
        ]

        for course_info in courses_catalog:
            course_obj, _ = Course.objects.update_or_create(
                slug=course_info['slug'],
                defaults={
                    'title': course_info['title'],
                    'description': course_info['description'],
                    'is_published': True
                }
            )
            for mod_info in course_info['modules']:
                Module.objects.update_or_create(
                    course=course_obj,
                    order=mod_info['order'],
                    defaults={
                        'title': mod_info['title'],
                        'video_url': mod_info['video_url'],
                        'content': mod_info['content'],
                        'reflection_prompt': mod_info['reflection_prompt']
                    }
                )

        self.stdout.write(self.style.SUCCESS("Seeded 3 evidence-based courses (Anxiety, EQ RULER, Self-Compassion) and their modules."))
        self.stdout.write(self.style.SUCCESS("Database seeding completed successfully!"))
