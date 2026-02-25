from collections import Counter
from .ml_engine import StudentRecommendationEngine
from .models import Recommendation, RecommendationSession


def calculate_riasec_scores(student_profile) -> dict:
    """
    Calculate RIASEC scores from individual PsychometricResponse records.
    Returns dict like: {'REALISTIC': 4.2, 'INVESTIGATIVE': 3.8, ...}
    
    NOTE: PsychometricResponse links to Profile (student), not User directly
    """
    from django.apps import apps
    PsychometricResponse = apps.get_model('assessment', 'PsychometricResponse')
    
    # ── Get responses for this student's profile ──
    responses = PsychometricResponse.objects.filter(
        student=student_profile,  # ← Fixed: 'student' not 'user'
        question__category__in=[
            'REALISTIC', 'INVESTIGATIVE', 'ARTISTIC',
            'SOCIAL', 'ENTERPRISING', 'CONVENTIONAL'
        ]
    ).select_related('question')

    # Group by category and calculate average rating
    category_scores = {}
    category_counts = Counter()

    for response in responses:
        category = response.question.category
        rating = response.response_value  # ← Fixed: 'response_value' not 'rating'
        
        if category not in category_scores:
            category_scores[category] = 0
        
        category_scores[category] += rating
        category_counts[category] += 1

    # Calculate averages
    riasec_scores = {}
    for category in ['REALISTIC', 'INVESTIGATIVE', 'ARTISTIC', 'SOCIAL', 'ENTERPRISING', 'CONVENTIONAL']:
        if category_counts[category] > 0:
            riasec_scores[category] = category_scores[category] / category_counts[category]
        else:
            riasec_scores[category] = 0.0

    return riasec_scores


def build_grades_list(student_profile) -> list[dict]:
    """
    Convert StudentGrades queryset into ML-ready list.
    StudentGrades has ForeignKey to Profile with related_name='grades'
    """
    grades = student_profile.grades.all()
    
    return [
        {
            'subject': g.subject,  # Already in correct format (e.g., 'MATHEMATICS')
            'grade':   g.grade     # Already in correct format (e.g., 'A', 'B+')
        }
        for g in grades
    ]


def build_preferences_dict(student_profile) -> dict:
    """
    Get StudentPreferences from the profile.
    StudentPreferences has OneToOne to Profile with related_name='preferences'
    """
    try:
        preferences = student_profile.preferences  # ← OneToOne, no .first() needed
        return {
            'preferred_subjects':      preferences.preferred_subjects or [],
            'preferred_career_fields': preferences.preferred_career_fields or [],
            'preferred_institutions':  preferences.preferred_institutions or [],
            'location_preference':     preferences.location_preference or '',
        }
    except Exception:
        # No preferences set (StudentPreferences doesn't exist for this profile)
        return {
            'preferred_subjects':      [],
            'preferred_career_fields': [],
            'preferred_institutions':  [],
            'location_preference':     '',
        }


def get_courses_data(courses_queryset) -> list[dict]:
    """
    Convert careers.Course queryset into ML-ready list.
    
    NOTE: Your Course model is missing these fields:
      - career_field
      - required_subjects
      - min_grade
    
    You'll need to add them to the Course model.
    """
    courses_data = []
    
    for course in courses_queryset:
        # Try to get fields if they exist, otherwise use defaults
        courses_data.append({
            'id':                course.id,
            'name':              course.name,
            'career_field':      getattr(course, 'career_field', '') or '',
            'required_subjects': list(getattr(course, 'required_subjects', []) or []),
            'min_grade':         getattr(course, 'min_grade', 'C') or 'C',
        })
    
    return courses_data


def get_universities_data(institutions_queryset) -> list[dict]:
    """
    Convert careers.Institution queryset into ML-ready list.
    """
    return [
        {
            'id':                 uni.id,
            'name':               uni.name,
            'location':           uni.location or '',
            'offered_course_ids': list(uni.courses.values_list('id', flat=True)),
        }
        for uni in institutions_queryset
    ]


def generate_student_recommendations(user) -> dict:
    """
    Full ML recommendation pipeline.
    
    Flow:
      1. Get student profile (grades, preferences)
      2. Calculate RIASEC scores from psychometric responses
      3. Fetch all courses and institutions
      4. Run ML engine
      5. Save results to Recommendation model
      6. Return results
    """
    from django.apps import apps

    # ── Get models ──
    Profile      = apps.get_model('students', 'Profile')
    Course       = apps.get_model('careers', 'Course')
    Institution  = apps.get_model('careers', 'Institution')

    # ── Get student profile ──
    try:
        student_profile = user.student_profile
    except Profile.DoesNotExist:
        return {
            "error": "Student profile not found. Please complete your profile first."
        }

    # ── Calculate RIASEC scores from psychometric test responses ──
    riasec_scores = calculate_riasec_scores(student_profile)  # ← Fixed: pass profile not user
    
    # Check if student has taken the test
    if not any(riasec_scores.values()):
        return {
            "error": "No psychometric assessment found. "
                     "Please complete the assessment at POST /api/assessment/submit/"
        }

    # ── Build student data ──
    grades_list      = build_grades_list(student_profile)
    preferences_dict = build_preferences_dict(student_profile)

    # ── Fetch all courses and institutions ──
    courses      = Course.objects.select_related('institution').all()
    universities = Institution.objects.prefetch_related('courses').all()

    courses_data      = get_courses_data(courses)
    universities_data = get_universities_data(universities)

    # ── Run ML engine ──
    engine  = StudentRecommendationEngine()
    results = engine.recommend(
        riasec_scores=riasec_scores,
        grades=grades_list,
        preferences=preferences_dict,
        courses=courses_data,
        universities=universities_data,
        top_courses=10,
        top_universities=5,
    )

    # ── Save to RecommendationSession ──
    session = RecommendationSession.objects.create(
        user=user,
        riasec_categories=results['student_profile']['top_riasec_categories'],
        avg_grade=results['student_profile']['avg_grade'],
        strong_subjects=results['student_profile']['strong_subjects'],
        matched_career_fields=results['student_profile']['matched_career_fields'],
    )

    # ── Save course recommendations ──
    for rec in results['recommended_courses']:
        course = Course.objects.get(id=rec['course_id'])
        
        Recommendation.objects.update_or_create(
            user=user,
            item_id=rec['course_id'],
            item_type='course',
            defaults={
                'item_name':           course.name,
                'score':               rec['score'],
                'recommendation_type': 'hybrid',
                'match_reasons':       rec['match_reasons'],
                'is_seen':             False,
            }
        )

    # ── Save university recommendations ──
    for rec in results['recommended_universities']:
        uni = Institution.objects.get(id=rec['university_id'])
        
        Recommendation.objects.update_or_create(
            user=user,
            item_id=rec['university_id'],
            item_type='institution',
            defaults={
                'item_name':           uni.name,
                'score':               rec['score'],
                'recommendation_type': 'hybrid',
                'match_reasons':       rec['match_reasons'],
                'is_seen':             False,
            }
        )

    return results