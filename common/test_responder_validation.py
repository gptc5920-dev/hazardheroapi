from datetime import timedelta

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase
from django.utils import timezone

from accounts.models import User
from accounts.serializers import UserSerializer
from alerts.serializers import ResponderAlertSerializer
from common.validators import (
    clean_string_list,
    validate_latitude,
    validate_phone_number,
)
from emergency_contacts.serializers import ResponderContactSerializer
from evacuation_centers.serializers import ResponderEvacuationSerializer
from go_bag.serializers import ResponderGoBagSerializer
from guidelines.models import Guideline
from guidelines.serializers import CitizenMediaSerializer, GuidelineMediaSerializer


class SharedInputValidatorTests(SimpleTestCase):
    def test_phone_coordinate_and_list_validation(self):
        validate_phone_number('+63 (917) 123-4567')
        validate_latitude('8.5')
        self.assertEqual(clean_string_list(['Flood', ' Flood ']), ['Flood'])

        with self.assertRaises(ValidationError):
            validate_phone_number('call-me')
        with self.assertRaises(ValidationError):
            validate_latitude('91')
        with self.assertRaises(ValidationError):
            clean_string_list('Flood')


class ResponderSerializerValidationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='existing@example.com',
            password='StrongPass123!',
            first_name='Existing',
            last_name='Responder',
        )

    def test_account_requires_password_and_case_insensitive_unique_email(self):
        missing_password = UserSerializer(
            data={
                'email': 'new@example.com',
                'first_name': 'New',
                'last_name': 'Responder',
            }
        )
        self.assertFalse(missing_password.is_valid())
        self.assertIn('password', missing_password.errors)

        duplicate = UserSerializer(
            data={
                'email': 'EXISTING@example.com',
                'first_name': 'Other',
                'last_name': 'Responder',
                'password': 'StrongPass123!',
            }
        )
        self.assertFalse(duplicate.is_valid())
        self.assertIn('email', duplicate.errors)

    def test_go_bag_rejects_zero_quantity_and_blank_unit(self):
        valid_data = {
            'name': 'First Aid Kit',
            'description': 'Medical supplies',
            'category': 'Medical Supplies',
            'quantity': 1,
            'unit': 'kit',
            'priority_level': 'High',
        }
        blank_unit = ResponderGoBagSerializer(data={**valid_data, 'unit': '   '})
        self.assertFalse(blank_unit.is_valid())
        self.assertIn('unit', blank_unit.errors)

        zero_quantity = ResponderGoBagSerializer(
            data={**valid_data, 'quantity': 0}
        )
        self.assertFalse(zero_quantity.is_valid())
        self.assertIn('quantity', zero_quantity.errors)

    def test_evacuation_center_rejects_invalid_location_phone_and_capacity(self):
        base = {
            'name': 'Central School',
            'center_code': 'EC-100',
            'region': 'IX',
            'province': 'Zamboanga del Norte',
            'city_municipality': 'Dipolog',
            'barangay': 'Central',
            'street_address': 'Main Street',
            'latitude': '91',
            'longitude': '123.28',
            'total_capacity': 10,
            'current_occupancy': 11,
            'contact_person': 'Officer',
            'contact_number': 'not-a-phone',
            'facility_type': 'School',
            'supported_emergency_types': ['Flood'],
        }
        serializer = ResponderEvacuationSerializer(data=base)
        self.assertFalse(serializer.is_valid())
        self.assertIn('latitude', serializer.errors)
        self.assertIn('contact_number', serializer.errors)

        base.update(latitude='8.5', contact_number='911')
        serializer = ResponderEvacuationSerializer(data=base)
        self.assertFalse(serializer.is_valid())
        self.assertIn('current_occupancy', serializer.errors)

    def test_contact_and_alert_reject_malformed_data(self):
        contact = ResponderContactSerializer(
            data={
                'organization_name': 'City Rescue',
                'contact_type': 'Rescue Team',
                'primary_phone_number': 'rescue-now',
                'region': 'IX',
                'province': 'Zamboanga del Norte',
                'city_municipality': 'Dipolog',
                'barangay': 'Central',
                'availability': '24/7',
                'emergency_types': ['Flood'],
            }
        )
        self.assertFalse(contact.is_valid())
        self.assertIn('primary_phone_number', contact.errors)

        alert = ResponderAlertSerializer(
            data={
                'title': 'Flood warning',
                'message': 'Water is rising.',
                'instructions': '',
                'alert_type': 'Flood',
                'severity_level': 'Critical',
                'source': 'CDRRMO',
                'latitude': '8.5',
                'affected_areas': [],
                'evacuation_required': True,
                'starts_at': timezone.now(),
                'expires_at': timezone.now() + timedelta(hours=1),
            }
        )
        self.assertFalse(alert.is_valid())
        self.assertIn('location', alert.errors)
        self.assertIn('instructions', alert.errors)
        self.assertIn('affected_areas', alert.errors)

    def test_guideline_media_accepts_embeds_and_safe_svg_uploads(self):
        guideline = Guideline.objects.create(
            title='Media Safety',
            summary='Media summary',
            content='Media content',
            category='Safety Procedures',
            emergency_type='General Emergency',
        )
        linked = GuidelineMediaSerializer(
            data={
                'guideline': str(guideline.pk),
                'source_type': 'link',
                'media_type': 'video',
                'title': 'Preparedness video',
                'external_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            }
        )
        self.assertTrue(linked.is_valid(), linked.errors)
        media = linked.save()
        public = CitizenMediaSerializer(media, context={'language': 'en'}).data
        self.assertEqual(public['provider'], 'youtube')
        self.assertEqual(public['media_url'], media.external_url)

        invalid_link = GuidelineMediaSerializer(
            data={
                'guideline': str(guideline.pk),
                'source_type': 'link',
                'media_type': 'video',
                'title': 'Invalid video page',
                'external_url': 'https://www.youtube.com/',
            }
        )
        self.assertFalse(invalid_link.is_valid())
        self.assertIn('external_url', invalid_link.errors)

        svg = GuidelineMediaSerializer(
            data={
                'guideline': str(guideline.pk),
                'source_type': 'upload',
                'media_type': 'svg',
                'title': 'Evacuation icon',
                'media_file': SimpleUploadedFile(
                    'evacuation.svg',
                    b'<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0"/></svg>',
                    content_type='image/svg+xml',
                ),
            }
        )
        self.assertTrue(svg.is_valid(), svg.errors)

        unsafe_svg = GuidelineMediaSerializer(
            data={
                'guideline': str(guideline.pk),
                'source_type': 'upload',
                'media_type': 'svg',
                'title': 'Unsafe icon',
                'media_file': SimpleUploadedFile(
                    'unsafe.svg',
                    b'<svg xmlns="http://www.w3.org/2000/svg"><script/></svg>',
                    content_type='image/svg+xml',
                ),
            }
        )
        self.assertFalse(unsafe_svg.is_valid())
        self.assertIn('media_file', unsafe_svg.errors)
