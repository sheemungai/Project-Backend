from .ml_engine import StudentRecommendationEngine
from .models import Recommendation


def build_riasec_scores(assessment_result) -> dict:
    """
    Convert AssessmentResult RIASEC scores into a dict.
    Matches your assessment app's AssessmentResult model fields.
    """
    return {
        'REALISTIC':     float(getattr(assessment_result, 'realistic_score', 0) or 0),
        'INVESTIGATIVE': float(getattr(assessment_result, 'investigative_score', 0) or 0),
        'ARTISTIC':      float(getattr(assessment_result, 'artistic_score', 0) or 0),
        'SOCIAL':        float(getattr(assessment_result, 'social_score', 0) or 0),
        'ENTERPRISING':  float(getattr(assessment_result, 'enterprising_score', 0) or 0),
        'CONVENTIONAL':  float(getattr(assessment_result, 'conventional_score', 0) or 0),
    }


def build_grades_list(grades_queryset) -> list[dict]:
    """
    Convert grades queryset into ML-ready list.
    Matches your grades app Grade model (subject, grade fields).
    """
    return [
        {
            'subject': g.subject.upper(),
            'grade':   g.grade
        }
        for g in grades_queryset
    ]


def build_preferences_dict(preferences_obj) -> dict:
    """
    Convert StudentPreference model into a dict.
    Matches your preferences app fields:
      preferred_subjects, preferred_career_fields,
      preferred_institutions, location_preference
    """
    if not preferences_obj:
        return {
            'preferred_subjects':      [],
            'preferred_career_fields': [],
            'preferred_institutions':  [],
            'location_preference':     '',
        }
    return {
        'preferred_subjects':      preferences_obj.preferred_subjects or [],
        'preferred_career_fields': preferences_obj.preferred_career_fields or [],
        'preferred_institutions':  preferences_obj.preferred_institutions or [],
        'location_preference':     preferences_obj.location_preference or '',
    }


def get_courses_data(courses_queryset) -> list[dict]:
    """
    Convert courses queryset into ML-ready list.
    Matches your courses app Course model.
    """
    return [
        {
            'id':               course.id,
            'name':             course.name,
            'career_field':     getattr(course, 'career_field', '') or '',
            'required_subjects': list(getattr(course, 'required_subjects', []) or []),
            'min_grade':        getattr(course, 'min_grade', 'C') or 'C',
        }
        for course in courses_queryset
    ]


def get_universities_data(universities_queryset) -> list[dict]:
    """
    Convert institutions queryset into ML-ready list.
    Matches your institutions app Institution model.
    Uses prefetch_related('courses') for efficiency.
    """
    return [
        {
            'id':                 uni.id,
            'name':               uni.name,
            'location':           getattr(uni, 'location', '') or '',
            'offered_course_ids': list(uni.courses.values_list('id', flat=True)),
        }
        for uni in universities_queryset
    ]


def generate_student_recommendations(user) -> dict:
    """
    Full pipeline:
      1. Fetch student's assessment result, grades, preferences
      2. Fetch all courses and institutions from DB
      3. Run ML engine
      4. Save results to Recommendation model
      5. Return results

    Called after the student submits their psychometric test
    via POST /api/assessment/submit/
    """
    from django.apps import apps

    # ── Dynamically import models to avoid circular imports ──
    # Adjust these app/model names to match your actual Django apps
    Grade            = apps.get_model('grades', 'Grade')
    StudentPreference = apps.get_model('preferences', 'StudentPreference')
    Course           = apps.get_model('courses', 'Course')
    Institution      = apps.get_model('institutions', 'Institution')
    AssessmentResult = apps.get_model('assessment', 'AssessmentResult')

    # ── Fetch the student's latest psychometric result ──
    assessment_result = (
        AssessmentResult.objects
        .filter(user=user)
        .order_by('-created_at')
        .first()
    )

    if not assessment_result:
        return {
            "error": "No psychometric assessment found. "
                     "Please complete the assessment at POST /api/assessment/submit/"
        }

    # ── Fetch student data ──
    grades      = Grade.objects.filter(user=user)
    preferences = StudentPreference.objects.filter(user=user).first()

    # ── Fetch all courses and institutions ──
    courses      = Course.objects.all()
    universities = Institution.objects.prefetch_related('courses').all()

    # ── Build ML inputs ──
    riasec_scores     = build_riasec_scores(assessment_result)
    grades_list       = build_grades_list(grades)
    preferences_dict  = build_preferences_dict(preferences)
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

    # ── Save course recommendations to DB ──
    for rec in results['recommended_courses']:
        Recommendation.objects.update_or_create(
            user=user,
            item_id=rec['course_id'],
            item_type='course',
            defaults={
                'score':               rec['score'],
                'recommendation_type': 'hybrid',
                'is_seen':             False,
            }
        )

    # ── Save university recommendations to DB ──
    for rec in results['recommended_universities']:
        Recommendation.objects.update_or_create(
            user=user,
            item_id=rec['university_id'],
            item_type='university',
            defaults={
                'score':               rec['score'],
                'recommendation_type': 'hybrid',
                'is_seen':             False,
            }
        )

    return results