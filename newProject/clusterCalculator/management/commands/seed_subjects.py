from django.core.management.base import BaseCommand
from django.db import transaction

from clusterCalculator.models import Subject

SUBJECT_DEFINITIONS = [
    {"name": "English", "code": "101", "is_compulsory": True},
    {"name": "Kiswahili", "code": "102", "is_compulsory": True},
    {"name": "Mathematics", "code": "121", "is_compulsory": True},
    {"name": "Biology", "code": "231", "is_compulsory": False},
    {"name": "Chemistry", "code": "233", "is_compulsory": False},
    {"name": "Physics", "code": "232", "is_compulsory": False},
    {"name": "History", "code": "311", "is_compulsory": False},
    {"name": "Geography", "code": "312", "is_compulsory": False},
    {"name": "Christian Religious Education", "code": "313", "is_compulsory": False},
    {"name": "Islamic Religious Education", "code": "314", "is_compulsory": False},
    {"name": "Hindu Religious Education", "code": "315", "is_compulsory": False},
    {"name": "French", "code": "501", "is_compulsory": False},
    {"name": "German", "code": "502", "is_compulsory": False},
    {"name": "Arabic", "code": "503", "is_compulsory": False},
    {"name": "Home Science", "code": "511", "is_compulsory": False},
    {"name": "Agriculture", "code": "443", "is_compulsory": False},
    {"name": "Woodwork", "code": "441", "is_compulsory": False},
    {"name": "Metalwork", "code": "442", "is_compulsory": False},
    {"name": "Building Construction", "code": "445", "is_compulsory": False},
    {"name": "Power Mechanics", "code": "447", "is_compulsory": False},
    {"name": "Electricity", "code": "448", "is_compulsory": False},
    {"name": "Drawing and Design", "code": "444", "is_compulsory": False},
    {"name": "Aviation Technology", "code": "449", "is_compulsory": False},
    {"name": "Computer Studies", "code": "451", "is_compulsory": False},
    {"name": "Business Studies", "code": "565", "is_compulsory": False},
    {"name": "Music", "code": "521", "is_compulsory": False},
    {"name": "Art and Design", "code": "522", "is_compulsory": False},
]


class Command(BaseCommand):
    help = "Seed the Subject table with the standard KCSE subject list so that cluster mappings work."

    def handle(self, *args, **options):
        created = 0
        updated = 0

        self.stdout.write("Seeding KCSE subjects...")

        with transaction.atomic():
            for definition in SUBJECT_DEFINITIONS:
                subject, is_created = Subject.objects.update_or_create(
                    name=definition["name"],
                    defaults={
                        "code": definition["code"],
                        "is_compulsory": definition["is_compulsory"],
                    },
                )

                if is_created:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Subject seeding complete. Created {created}, updated {updated}."
            )
        )
