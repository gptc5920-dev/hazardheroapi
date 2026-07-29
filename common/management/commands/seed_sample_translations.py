from django.core.management.base import BaseCommand
from django.db import transaction

from alerts.models import EmergencyAlert, EmergencyAlertTranslation
from emergency_contacts.models import (
    EmergencyContact,
    EmergencyContactTranslation,
)
from evacuation_centers.models import (
    EvacuationCenter,
    EvacuationCenterTranslation,
)
from go_bag.models import GoBagItem, GoBagItemTranslation
from guidelines.models import Guideline, GuidelineTranslation
from languages.models import Language


SAMPLE_TRANSLATIONS = {
    "fil": {
        "guideline": {
            "translated_title": "Mga Pangunahing Hakbang sa Kaligtasan sa Lindol",
            "translated_summary": "Dumapa, magkubli, at kumapit.",
            "translated_content": (
                "Lumayo sa mga bintana at protektahan ang iyong ulo at leeg."
            ),
            "translated_safety_instructions": "Dumapa, magkubli, at kumapit.",
        },
        "alert": {
            "translated_title": "Halimbawang Abiso sa Panahon",
            "translated_message": (
                "Subaybayan ang mga opisyal na update sa panahon."
            ),
            "translated_instructions": (
                "Ihanda ang iyong Go Bag at manatiling alerto."
            ),
            "translated_affected_area_description": "",
        },
        "go_bag": {
            "translated_name": "Inuming Tubig",
            "translated_description": (
                "Mag-imbak ng hindi bababa sa tatlong litro bawat tao bawat araw."
            ),
        },
        "center": {
            "translated_description": (
                "Pangunahing evacuation site ng lungsod."
            ),
            "translated_facility_description": "",
        },
        "contact": {
            "translated_description": (
                "Dalawampu't apat na oras na koordinasyon para sa emerhensiya."
            ),
        },
    },
    "ceb": {
        "guideline": {
            "translated_title": (
                "Pangunang mga Lakang sa Kaluwasan Panahon sa Linog"
            ),
            "translated_summary": "Dapa, panalipod, ug kupot.",
            "translated_content": (
                "Palayo sa mga bintana ug panalipdi ang imong ulo ug liog."
            ),
            "translated_safety_instructions": "Dapa, panalipod, ug kupot.",
        },
        "alert": {
            "translated_title": "Pananglitan nga Pahibalo sa Panahon",
            "translated_message": (
                "Sunda ang opisyal nga mga update sa panahon."
            ),
            "translated_instructions": (
                "Andama ang imong Go Bag ug magpabiling alerto."
            ),
            "translated_affected_area_description": "",
        },
        "go_bag": {
            "translated_name": "Inimnong Tubig",
            "translated_description": (
                "Pagtipig og labing menos tulo ka litro matag tawo kada adlaw."
            ),
        },
        "center": {
            "translated_description": (
                "Pangunang evacuation site sa siyudad."
            ),
            "translated_facility_description": "",
        },
        "contact": {
            "translated_description": (
                "Baynte-kuwatro oras nga koordinasyon sa emerhensiya."
            ),
        },
    },
}


class Command(BaseCommand):
    help = "Publish Filipino and Bisaya translations for bundled sample data."

    @transaction.atomic
    def handle(self, *args, **options):
        parents = {
            "guideline": Guideline.objects.filter(
                pk="22222222-2222-4222-8222-222222222222"
            ).first(),
            "alert": EmergencyAlert.objects.filter(
                pk="55555555-5555-4555-8555-555555555555"
            ).first(),
            "go_bag": GoBagItem.objects.filter(
                pk="11111111-1111-4111-8111-111111111111"
            ).first(),
            "center": EvacuationCenter.objects.filter(
                pk="33333333-3333-4333-8333-333333333333"
            ).first(),
            "contact": EmergencyContact.objects.filter(
                pk="44444444-4444-4444-8444-444444444444"
            ).first(),
        }
        translation_models = {
            "guideline": (GuidelineTranslation, "guideline"),
            "alert": (EmergencyAlertTranslation, "alert"),
            "go_bag": (GoBagItemTranslation, "item"),
            "center": (EvacuationCenterTranslation, "center"),
            "contact": (EmergencyContactTranslation, "contact"),
        }

        changed = 0
        for language_code, module_values in SAMPLE_TRANSLATIONS.items():
            language = Language.objects.get(language_code=language_code)
            for module, translated_fields in module_values.items():
                parent = parents[module]
                if parent is None:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Skipped {module} ({language_code}); "
                            "load fixtures/sample_data.json first."
                        )
                    )
                    continue
                model, parent_field = translation_models[module]
                lookup = {parent_field: parent, "language": language}
                _, created = model.objects.update_or_create(
                    **lookup,
                    defaults={
                        **translated_fields,
                        "status": "Published",
                    },
                )
                changed += 1
                action = "Created" if created else "Updated"
                self.stdout.write(f"{action} {module} translation ({language_code}).")

        self.stdout.write(
            self.style.SUCCESS(f"Published {changed} sample translations.")
        )
