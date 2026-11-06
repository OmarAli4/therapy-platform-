import json
from datetime import date, timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.management import call_command
from appointments.models import Appointment

User = get_user_model()


class KindSoulEndToEndTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_data')

    def setUp(self):
        self.client_http = Client()

    def test_public_pages_and_dark_theme_integrity(self):
        for url_name in ['landing', 'calm_space', 'book_session', 'course_list', 'login', 'register']:
            response = self.client_http.get(reverse(url_name))
            self.assertEqual(response.status_code, 200, f"{url_name} failed to load")
            html = response.content.decode('utf-8')
            # Ensure broken undefined classes are completely gone
            self.assertNotIn('text-charcoal-900', html, f"Broken class text-charcoal-900 found in {url_name}")
            self.assertNotIn('bg-beige-50', html, f"Broken class bg-beige-50 found in {url_name}")

    def test_multi_therapist_slots_and_booking_flow(self):
        therapists = User.objects.filter(role=User.Role.THERAPIST)
        self.assertGreaterEqual(therapists.count(), 3)

        dr_wessam = therapists.filter(username='therapist@sanctuary.com').first()
        self.assertIsNotNone(dr_wessam)

        # Find next Monday
        today = date.today()
        next_monday = today + timedelta(days=(7 - today.weekday()))
        res = self.client_http.get(
            reverse('available_slots_api'),
            {'date': next_monday.strftime('%Y-%m-%d'), 'therapist_id': dr_wessam.id}
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['therapist_id'], dr_wessam.id)
        self.assertTrue(len(data['slots']) > 0)

        # Book a slot as logged-in client
        self.client_http.login(username='client@sanctuary.com', password='password123')
        first_slot = data['slots'][0]
        book_res = self.client_http.post(reverse('book_session'), {
            'therapist_id': dr_wessam.id,
            'focus_area': 'ANXIETY',
            'date': next_monday.strftime('%Y-%m-%d'),
            'start_time': first_slot['start_time'],
            'end_time': first_slot['end_time'],
            'notes_by_client': 'Testing multi-therapist booking',
        })
        self.assertEqual(book_res.status_code, 200)
        self.assertTrue(Appointment.objects.filter(therapist=dr_wessam, date=next_monday).exists())

    def test_therapist_dashboard_and_schedule_update(self):
        self.client_http.login(username='layla@sanctuary.com', password='password123')
        dash_res = self.client_http.get(reverse('therapist_dashboard'))
        self.assertEqual(dash_res.status_code, 200)

        update_res = self.client_http.post(reverse('update_therapist_availability'), {
            'is_active_0': 'on',
            'start_time_0': '10:00',
            'end_time_0': '16:00',
            'buffer_0': '15',
        })
        self.assertEqual(update_res.status_code, 302)
