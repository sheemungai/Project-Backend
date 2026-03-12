from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from clusterCalculator.models import Cluster, Subject

CLUSTER_DEFINITIONS = [
    {
        "name": "Engineering & Physical Sciences",
        "code": "CLUSTER_ENGINEERING",
        "description": "Programmes that emphasize mathematics, physics, chemistry, and technical drawing.",
        "subjects": [
            "Mathematics",
            "Physics",
            "Chemistry",
            "Computer Studies",
            "Drawing and Design",
        ],
    },
    {
        "name": "Medicine & Life Sciences",
        "code": "CLUSTER_MEDICINE",
        "description": "Health, biological, and life-science oriented programmes.",
        "subjects": [
            "Biology",
            "Chemistry",
            "Mathematics",
            "English",
            "Kiswahili",
        ],
    },
    {
        "name": "Arts & Humanities",
        "code": "CLUSTER_ARTS",
        "description": "Humanities, languages, social sciences, and liberal arts programmes.",
        "subjects": [
            "English",
            "Kiswahili",
            "History",
            "Geography",
            "Christian Religious Education",
        ],
    },
    {
        "name": "Business & ICT",
        "code": "CLUSTER_BUSINESS",
        "description": "Commerce, economics, ICT, and entrepreneurship related programmes.",
        "subjects": [
            "Mathematics",
            "Business Studies",
            "Computer Studies",
            "English",
            "Geography",
        ],
    },
    {
        "name": "Technology & Computing",
        "code": "CLUSTER_TECH",
        "description": "Pure tech pathways focusing on computing, engineering math, and problem solving.",
        "subjects": [
            "Mathematics",
            "Physics",
            "Computer Studies",
            "English",
            "Business Studies",
        ],
    },
    {
        "name": "Agriculture & Environmental Sciences",
        "code": "CLUSTER_AGRICULTURE",
        "description": "Agriculture, environmental management, and natural resource programmes.",
        "subjects": [
            "Agriculture",
            "Biology",
            "Chemistry",
            "Geography",
            "Mathematics",
        ],
    },
    {
        "name": "Home Science & Creative Arts",
        "code": "CLUSTER_HOME_SCIENCE",
        "description": "Home science, design, and creative industry programmes.",
        "subjects": [
            "Home Science",
            "Art and Design",
            "Music",
            "English",
            "Business Studies",
        ],
    },
]


class Command(BaseCommand):
    help = (
        "Seed the Cluster table with a starter set of clusters and attach at least four subjects to each "
        "(requires `seed_subjects` to have run first)."
    )

    def handle(self, *args, **options):
        subjects = Subject.objects.all()
        if not subjects.exists():
            raise CommandError(
                "No subjects found. Run `python manage.py seed_subjects` before seeding clusters."
            )

        lookup = {subject.name.lower(): subject for subject in subjects}
        missing_subjects = set()

        created = 0
        updated = 0

        with transaction.atomic():
            for definition in CLUSTER_DEFINITIONS:
                subject_objs = []
                for name in definition["subjects"]:
                    subject = lookup.get(name.lower())
                    if not subject:
                        missing_subjects.add(name)
                    else:
                        subject_objs.append(subject)

                if missing_subjects:
                    missing = ", ".join(sorted(missing_subjects))
                    raise CommandError(
                        f"Cannot seed clusters because the following subjects are missing: {missing}. "
                        "Run `seed_subjects` or add them manually first."
                    )

                cluster, is_created = Cluster.objects.update_or_create(
                    code=definition["code"],
                    defaults={
                        "name": definition["name"],
                        "description": definition["description"],
                    },
                )

                cluster.subjects.set(subject_objs)

                if is_created:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Cluster seeding complete. Created {created}, updated {updated}."
            )
        )
