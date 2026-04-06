from django.core.management.base import BaseCommand
from assessment.models import PsychometricQuestion


class Command(BaseCommand):
    help = 'Populate optimized psychometric questions (18 total - RIASEC only)'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Creating 18 optimized RIASEC questions...'))
        
        # OPTIMAL 18-QUESTION DISTRIBUTION
        # 3 questions per RIASEC category (6 categories × 3 = 18 total)
        questions_data = {
            'REALISTIC': [
                "I enjoy working with tools, machines, and hands-on equipment",
                "I like working outdoors or in physical environments",
                "I prefer practical, hands-on work over desk work"
            ],
            'INVESTIGATIVE': [
                "I enjoy solving complex problems and puzzles",
                "I like conducting research and analyzing data",
                "I am curious about understanding how things work"
            ],
            'ARTISTIC': [
                "I enjoy creative activities like art, design, or writing",
                "I like expressing myself through creative projects",
                "I appreciate beauty, aesthetics, and original ideas"
            ],
            'SOCIAL': [
                "I enjoy helping, teaching, or counseling others",
                "I like working closely with people in teams",
                "I am good at understanding and supporting others' needs"
            ],
            'ENTERPRISING': [
                "I enjoy leading projects and influencing others",
                "I like taking risks and pursuing business opportunities",
                "I am comfortable persuading people and public speaking"
            ],
            'CONVENTIONAL': [
                "I enjoy organizing data and maintaining records",
                "I like following clear procedures and structured tasks",
                "I am detail-oriented and thorough in my work"
            ]
        }
        
        created_count = 0
        updated_count = 0
        
        # First, deactivate ALL existing questions to start fresh
        self.stdout.write('Clearing existing questions...')
        PsychometricQuestion.objects.all().update(is_active=False)
        
        # Create/activate the new 18 questions
        for category, questions in questions_data.items():
            for question_text in questions:
                obj, created = PsychometricQuestion.objects.get_or_create(
                    question_text=question_text,
                    category=category,
                    defaults={'is_active': True}
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(f'✓ Created [{category}]: {question_text[:50]}...')
                else:
                    # If it already exists, just activate it
                    if not obj.is_active:
                        obj.is_active = True
                        obj.save()
                        updated_count += 1
                        self.stdout.write(f'✓ Activated [{category}]: {question_text[:50]}...')
                    else:
                        self.stdout.write(f'→ Already exists [{category}]: {question_text[:50]}...')
        
        total_active = PsychometricQuestion.objects.filter(is_active=True).count()
        
        self.stdout.write(self.style.SUCCESS(f'\n=== Complete ==='))
        self.stdout.write(self.style.SUCCESS(f'Created: {created_count} new questions'))
        self.stdout.write(self.style.SUCCESS(f'Activated: {updated_count} existing questions'))
        self.stdout.write(self.style.SUCCESS(f'Total active questions: {total_active}'))
        
        # Show detailed breakdown
        self.stdout.write('\n--- Final Question Distribution ---')
        for category in sorted(questions_data.keys()):
            count = PsychometricQuestion.objects.filter(
                category=category, 
                is_active=True
            ).count()
            bar = '█' * count + '░' * (3 - count)
            self.stdout.write(f'{category:15} : {count} question{"s" if count != 1 else " "} {bar}')
        
        self.stdout.write(f'\n📊 Summary:')
        self.stdout.write(f'   Total questions: {total_active}')
        self.stdout.write(f'   Categories: 6 (3 questions each)')
        self.stdout.write(f'   Estimated completion time: 4-5 minutes')