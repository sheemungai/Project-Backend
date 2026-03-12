from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from careers.models import CareerPath, Course

CAREER_PATH_DEFINITIONS = [
    {
        "name": "Software Engineering",
        "description": (
            "Design, develop, test, and deploy software solutions that power web, mobile, and enterprise platforms. "
            "This pathway emphasises clean code, agile delivery, and continuous integration."
        ),
        "required_skills": "Mathematics,Physics,English/Kiswahili,Python/JavaScript, algorithms, version control, cloud services, teamwork",
        "average_salary": Decimal("1800000.00"),
        "course_codes": ["BSC-CS", "BSC-IT"],
        "course_filters": ["Computer Science", "Software", "Information Technology"],
    },
    {
        "name": "Data Science & AI",
        "description": (
            "Transform raw data into actionable insights using statistics, machine learning, and AI systems. "
            "Ideal for students who enjoy maths, coding, and experimentation."
        ),
        "required_skills": "Mathematics,Physics,English/Kiswahili,Python/R, statistics, machine learning, SQL, data storytelling",
        "average_salary": Decimal("1900000.00"),
        "course_codes": ["BSC-DS"],
        "course_filters": ["Data Science", "Artificial Intelligence", "Analytics"],
    },
    {
        "name": "Medicine & Health Sciences",
        "description": (
            "Deliver preventative and curative health services through clinical practice, research, or public health programmes."
        ),
        "required_skills": "Mathematics,Physics,English/Kiswahili,Biology, chemistry, empathy, decision making, attention to detail",
        "average_salary": Decimal("2400000.00"),
        "course_codes": ["MBChB", "NURSING-BSC"],
        "course_filters": ["Medicine", "Surgery", "Nursing", "Pharmacy"],
    },
    {
        "name": "Civil & Structural Engineering",
        "description": (
            "Plan, design, and supervise infrastructure projects such as roads, bridges, and smart cities with sustainability in mind."
        ),
        "required_skills": "Mathematics,Physics,English/Kiswahili,physics, CAD, project management, problem solving",
        "average_salary": Decimal("2000000.00"),
        "course_codes": ["BSC-CIVIL"],
        "course_filters": ["Civil", "Structural", "Construction"],
    },
    {
        "name": "Business, Finance & Entrepreneurship",
        "description": (
            "Drive organisational growth through strategy, finance, marketing, and innovation. Ideal for aspiring founders and managers."
        ),
        "required_skills": "Mathematics,English/Kiswahili,Accounting, communication, leadership, negotiation, analytics",
        "average_salary": Decimal("1500000.00"),
        "course_codes": ["BCOM-GEN", "BBIT"],
        "course_filters": ["Business", "Commerce", "Finance", "Entrepreneurship", "Economics"],
    },
    {
        "name": "Agriculture & Environmental Management",
        "description": (
            "Improve food security and protect natural resources through modern farming, agribusiness, and conservation initiatives."
        ),
        "required_skills": "Mathematics,English/Kiswahili,Biology, agronomy, GIS, sustainability, problem solving",
        "average_salary": Decimal("1300000.00"),
        "course_codes": ["BSC-AGRIC"],
        "course_filters": ["Agriculture", "Environmental", "Natural Resource"],
    },
    {
        "name": "Creative Media & Design",
        "description": (
            "Blend art, storytelling, and technology to produce compelling visual content for digital platforms, advertising, and entertainment."
        ),
        "required_skills": "Mathematics,English/Kiswahili,Graphic design, UI/UX, video editing, creativity, collaboration",
        "average_salary": Decimal("1200000.00"),
        "course_codes": ["BA-DESIGN"],
        "course_filters": ["Design", "Media", "Film", "Fine Art"],
    },
]


class Command(BaseCommand):
    help = "Seed or refresh curated career paths so the frontend can display rich pathways linked to courses."

    def handle(self, *args, **options):
        total_courses = Course.objects.count()
        if total_courses == 0:
            self.stdout.write(
                self.style.WARNING(
                    "No courses found. Run `import_kuccps_data` or create courses before attaching them to career paths."
                )
            )

        created = 0
        updated = 0
        missing_course_codes = set()

        with transaction.atomic():
            for definition in CAREER_PATH_DEFINITIONS:
                course_ids = set()

                codes = definition.get("course_codes", [])
                if codes:
                    matched_by_code = Course.objects.filter(prog_code__in=codes)
                    course_ids.update(matched_by_code.values_list("id", flat=True))
                    found_codes = set(matched_by_code.values_list("prog_code", flat=True))
                    missing_course_codes.update(set(codes) - found_codes)

                for keyword in definition.get("course_filters", []):
                    if keyword:
                        keyword_matches = Course.objects.filter(name__icontains=keyword)
                        course_ids.update(keyword_matches.values_list("id", flat=True))

                course_qs = Course.objects.filter(id__in=course_ids)

                career_path, is_created = CareerPath.objects.update_or_create(
                    name=definition["name"],
                    defaults={
                        "description": definition["description"],
                        "required_skills": definition["required_skills"],
                        "average_salary": definition.get("average_salary"),
                    },
                )

                career_path.related_courses.set(course_qs.distinct())

                if is_created:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Career path seeding complete. Created {created}, updated {updated}, total {CareerPath.objects.count()} paths."
            )
        )

        if missing_course_codes:
            formatted = ", ".join(sorted(missing_course_codes))
            self.stdout.write(
                self.style.WARNING(
                    f"Some course codes were not found and were skipped: {formatted}."
                )
            )
