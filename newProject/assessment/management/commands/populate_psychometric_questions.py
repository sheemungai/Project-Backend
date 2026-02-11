from django.core.management.base import BaseCommand
from assessment.models import PsychometricQuestion


class Command(BaseCommand):
    help = 'Populate psychometric test questions for RIASEC and Big Five'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Populating psychometric questions...'))
        
        # RIASEC Questions (10 questions per category = 60 total)
        riasec_questions = {
            'REALISTIC': [
                "I enjoy working with tools and machines",
                "I like working outdoors",
                "I prefer hands-on practical work",
                "I enjoy building and fixing things",
                "I like working with my hands",
                "I enjoy mechanical and technical activities",
                "I prefer physical work over desk work",
                "I like working with animals or plants",
                "I enjoy operating equipment and machinery",
                "I am good at repairing things"
            ],
            'INVESTIGATIVE': [
                "I enjoy solving complex problems",
                "I like conducting experiments and research",
                "I enjoy analyzing data and information",
                "I like learning about scientific concepts",
                "I enjoy working with numbers and formulas",
                "I like investigating how things work",
                "I prefer working independently on research",
                "I enjoy reading scientific articles",
                "I like thinking about abstract ideas",
                "I am curious about natural phenomena"
            ],
            'ARTISTIC': [
                "I enjoy creative and artistic activities",
                "I like expressing myself through art",
                "I enjoy writing stories or poems",
                "I like designing and creating things",
                "I enjoy music and performing arts",
                "I prefer unstructured and flexible work",
                "I like working in creative environments",
                "I enjoy using my imagination",
                "I like experimenting with new ideas",
                "I appreciate beauty and aesthetics"
            ],
            'SOCIAL': [
                "I enjoy helping and teaching others",
                "I like working with people",
                "I enjoy counseling and advising others",
                "I like working in teams",
                "I enjoy volunteering and community service",
                "I am good at understanding others' feelings",
                "I like resolving conflicts",
                "I enjoy caring for others",
                "I like organizing social events",
                "I prefer jobs that involve interaction"
            ],
            'ENTERPRISING': [
                "I enjoy leading and managing projects",
                "I like persuading and influencing others",
                "I enjoy starting new businesses or ventures",
                "I like taking risks and making decisions",
                "I enjoy selling and promoting ideas",
                "I am comfortable public speaking",
                "I like setting goals and achieving them",
                "I enjoy competitive environments",
                "I like organizing and delegating tasks",
                "I am good at motivating others"
            ],
            'CONVENTIONAL': [
                "I enjoy organizing and maintaining records",
                "I like following clear procedures and rules",
                "I enjoy working with data and details",
                "I like structured and orderly environments",
                "I enjoy administrative and clerical work",
                "I am good at keeping things organized",
                "I like working with systems and processes",
                "I enjoy tasks that require accuracy",
                "I prefer predictable work routines",
                "I am detail-oriented and thorough"
            ]
        }
        
        # Big Five Questions (10 questions per trait = 50 total)
        big_five_questions = {
            'OPENNESS': [
                "I have a vivid imagination",
                "I am interested in abstract ideas",
                "I enjoy trying new and different things",
                "I appreciate art and beauty",
                "I am curious about many things",
                "I enjoy thinking about complex problems",
                "I like to explore new places",
                "I am open to new experiences",
                "I enjoy learning about different cultures",
                "I like to consider multiple perspectives"
            ],
            'CONSCIENTIOUSNESS': [
                "I am always prepared and organized",
                "I follow through on my commitments",
                "I pay attention to details",
                "I like to have a plan and stick to it",
                "I am punctual and meet deadlines",
                "I keep my workspace tidy",
                "I complete tasks systematically",
                "I am reliable and dependable",
                "I think about consequences before acting",
                "I work hard to achieve my goals"
            ],
            'EXTRAVERSION': [
                "I enjoy being around people",
                "I feel comfortable in social situations",
                "I like to be the center of attention",
                "I am talkative and outgoing",
                "I make friends easily",
                "I enjoy parties and social gatherings",
                "I am energized by being with others",
                "I like to start conversations",
                "I am comfortable meeting new people",
                "I prefer working in groups"
            ],
            'AGREEABLENESS': [
                "I am considerate of others' feelings",
                "I like to help and support others",
                "I trust people easily",
                "I am cooperative and easy to work with",
                "I avoid conflicts and arguments",
                "I am sympathetic and compassionate",
                "I put others' needs before my own",
                "I am polite and respectful",
                "I forgive others easily",
                "I believe most people are good"
            ],
            'NEUROTICISM': [
                "I often feel stressed or anxious",
                "I worry about things that might go wrong",
                "My mood changes frequently",
                "I get upset easily",
                "I feel nervous in stressful situations",
                "I tend to overthink situations",
                "I am sensitive to criticism",
                "I sometimes feel sad or depressed",
                "I have difficulty handling pressure",
                "I get irritated by small things"
            ]
        }
        
        created_count = 0
        
        # Create RIASEC questions
        for category, questions in riasec_questions.items():
            for question_text in questions:
                question, created = PsychometricQuestion.objects.get_or_create(
                    question_text=question_text,
                    category=category,
                    defaults={'is_active': True}
                )
                if created:
                    created_count += 1
                    self.stdout.write(f'✓ Created: [{category}] {question_text[:50]}...')
        
        # Create Big Five questions
        for trait, questions in big_five_questions.items():
            for question_text in questions:
                question, created = PsychometricQuestion.objects.get_or_create(
                    question_text=question_text,
                    category=trait,
                    defaults={'is_active': True}
                )
                if created:
                    created_count += 1
                    self.stdout.write(f'✓ Created: [{trait}] {question_text[:50]}...')
        
        self.stdout.write(self.style.SUCCESS(f'\n=== Complete ==='))
        self.stdout.write(self.style.SUCCESS(f'Created {created_count} new questions'))
        self.stdout.write(self.style.SUCCESS(f'Total RIASEC questions: {PsychometricQuestion.objects.filter(category__in=["REALISTIC", "INVESTIGATIVE", "ARTISTIC", "SOCIAL", "ENTERPRISING", "CONVENTIONAL"]).count()}'))
        self.stdout.write(self.style.SUCCESS(f'Total Big Five questions: {PsychometricQuestion.objects.filter(category__in=["OPENNESS", "CONSCIENTIOUSNESS", "EXTRAVERSION", "AGREEABLENESS", "NEUROTICISM"]).count()}'))