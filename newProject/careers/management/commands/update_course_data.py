# careers/management/commands/update_course_data.py
from django.core.management.base import BaseCommand
from careers.models import Course

class Command(BaseCommand):
    help = 'Update courses with career fields and required subjects'

    def handle(self, *args, **options):
        self.stdout.write('Starting course data update...')
        
        # Mapping of course name patterns to career fields
        CAREER_FIELD_MAPPING = {
            # Computer Science & IT
            'INFORMATION TECHNOLOGY': 'Computer Science',
            'COMPUTER SCIENCE': 'Computer Science',
            'BUSINESS INFORMATION TECHNOLOGY': 'Computer Science',
            'SOFTWARE ENGINEERING': 'Computer Science',
            'DATA SCIENCE': 'Data Science',
            
            # Medicine & Health
            'MEDICINE': 'Medicine',
            'SURGERY': 'Medicine',
            'NURSING': 'Medicine',
            'PHARMACY': 'Medicine',
            'MEDICAL LABORATORY': 'Medicine',
            'CLINICAL MEDICINE': 'Medicine',
            'PUBLIC HEALTH': 'Public Health',
            
            # Engineering
            'ENGINEERING': 'Engineering',
            'ELECTRICAL': 'Engineering',
            'MECHANICAL': 'Engineering',
            'CIVIL': 'Engineering',
            'MECHATRONIC': 'Engineering',
            
            # Business
            'BUSINESS': 'Business',
            'COMMERCE': 'Business',
            'ACCOUNTING': 'Business',
            'FINANCE': 'Business',
            'ENTREPRENEURSHIP': 'Business',
            'MARKETING': 'Business',
            'SUPPLY CHAIN': 'Business',
            'PROCUREMENT': 'Business',
            'HUMAN RESOURCE': 'Business',
            'MANAGEMENT': 'Business',
            'LEADERSHIP': 'Business',
            
            # Education
            'EDUCATION': 'Education',
            'TEACHING': 'Education',
            'EARLY CHILDHOOD': 'Education',
            
            # Law
            'LAW': 'Law',
            'LLB': 'Law',
            
            # Architecture
            'ARCHITECTURE': 'Architecture',
            'ARCHITECTURAL': 'Architecture',
            
            # Economics & Statistics
            'ECONOMICS': 'Economics',
            'STATISTICS': 'Statistics',
            'ACTUARIAL': 'Statistics',
            
            # Psychology & Counseling
            'PSYCHOLOGY': 'Psychology',
            'COUNSELING': 'Psychology',
            'COUNSELLING': 'Psychology',
            
            # Media & Communication
            'JOURNALISM': 'Media',
            'COMMUNICATION': 'Media',
            'MASS COMMUNICATION': 'Media',
            'MEDIA': 'Media',
            'FILM': 'Media',
            'ANIMATION': 'Media',
            'GRAPHIC DESIGN': 'Media',
            
            # Agriculture
            'AGRICULTURE': 'Agriculture',
            'AGRIBUSINESS': 'Agriculture',
            'AGRICULTURAL': 'Agriculture',
            
            # Social Sciences
            'SOCIOLOGY': 'Social Sciences',
            'ANTHROPOLOGY': 'Social Sciences',
            'DEVELOPMENT STUDIES': 'Social Sciences',
            'COMMUNITY DEVELOPMENT': 'Social Sciences',
            'GENDER': 'Social Sciences',
            'SOCIAL WORK': 'Social Sciences',
            
            # Arts & Humanities
            'ARTS': 'Arts',
            'MUSIC': 'Arts',
            'FINE ARTS': 'Arts',
            'THEATRE': 'Arts',
            'KISWAHILI': 'Arts',
            'ENGLISH': 'Arts',
            'HISTORY': 'Arts',
            'GEOGRAPHY': 'Arts',
            'PHILOSOPHY': 'Arts',
            
            # Theology
            'THEOLOGY': 'Theology',
            'DIVINITY': 'Theology',
            'RELIGIOUS': 'Theology',
            'CHRISTIAN': 'Theology',
        }

        # Required subjects mapping by career field
        REQUIRED_SUBJECTS_MAPPING = {
            'Computer Science': ['MATHEMATICS', 'PHYSICS'],
            'Data Science': ['MATHEMATICS', 'PHYSICS'],
            'Engineering': ['MATHEMATICS', 'PHYSICS'],
            'Medicine': ['BIOLOGY', 'CHEMISTRY'],
            'Pharmacy': ['BIOLOGY', 'CHEMISTRY'],
            'Nursing': ['BIOLOGY', 'CHEMISTRY'],
            'Public Health': ['BIOLOGY', 'CHEMISTRY'],
            'Business': ['MATHEMATICS', 'BUSINESS'],
            'Accounting': ['MATHEMATICS', 'BUSINESS'],
            'Finance': ['MATHEMATICS', 'BUSINESS'],
            'Economics': ['MATHEMATICS', 'ECONOMICS'],
            'Statistics': ['MATHEMATICS'],
            'Education': ['ENGLISH'],
            'Law': ['ENGLISH', 'HISTORY'],
            'Architecture': ['MATHEMATICS', 'PHYSICS', 'GEOGRAPHY'],
            'Agriculture': ['BIOLOGY', 'CHEMISTRY', 'AGRICULTURE'],
            'Media': ['ENGLISH'],
            'Psychology': ['BIOLOGY', 'ENGLISH'],
            'Social Sciences': ['ENGLISH', 'GEOGRAPHY'],
            'Arts': ['ENGLISH'],
            'Theology': ['ENGLISH', 'HISTORY'],
        }

        updated_count = 0
        total_courses = Course.objects.count()
        
        for course in Course.objects.all():
            old_career_field = course.career_field
            old_required = course.required_subjects
            
            course_name_upper = course.name.upper()
            
            # Find matching career field
            for keyword, field in CAREER_FIELD_MAPPING.items():
                if keyword in course_name_upper:
                    course.career_field = field
                    break
            
            # If no match found, set a default based on common patterns
            if not course.career_field:
                if 'SCIENCE' in course_name_upper and 'COMPUTER' not in course_name_upper:
                    course.career_field = 'Science'
                elif 'BACHELOR OF ARTS' in course_name_upper:
                    course.career_field = 'Arts'
                else:
                    course.career_field = 'General'
            
            # Set required subjects based on career field
            if course.career_field in REQUIRED_SUBJECTS_MAPPING:
                course.required_subjects = REQUIRED_SUBJECTS_MAPPING[course.career_field]
            else:
                # Default required subjects
                course.required_subjects = ['MATHEMATICS', 'ENGLISH']
            
            # Only save if something changed
            if course.career_field != old_career_field or course.required_subjects != old_required:
                course.save()
                updated_count += 1
                self.stdout.write(f"Updated: {course.name[:50]}...")
                self.stdout.write(f"  → Career field: {course.career_field}")
                self.stdout.write(f"  → Required subjects: {course.required_subjects}")
        
        self.stdout.write(self.style.SUCCESS(f"\n✅ Successfully updated {updated_count} out of {total_courses} courses"))