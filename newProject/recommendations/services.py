# recommendations/services.py
from collections import Counter
from .ml_engine import StudentRecommendationEngine
from .models import Recommendation, RecommendationSession
from django.db.models import Prefetch


def calculate_riasec_scores(student_profile) -> dict:
    """
    Calculate RIASEC scores from individual PsychometricResponse records.
    Returns dict like: {'REALISTIC': 4.2, 'INVESTIGATIVE': 3.8, ...}
    
    NOTE: PsychometricResponse links to Profile (student), not User directly
    """
    from django.apps import apps
    PsychometricResponse = apps.get_model('assessment', 'PsychometricResponse')
    
    # Get responses for this student's profile
    responses = PsychometricResponse.objects.filter(
        student=student_profile,
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
        rating = response.response_value
        
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
    from students.utils import format_grades_for_ml
    
    grades = student_profile.grades.all()
    return format_grades_for_ml(grades)


def build_preferences_dict(student_profile) -> dict:
    """
    Get StudentPreferences from the profile.
    StudentPreferences has OneToOne to Profile with related_name='preferences'
    """
    try:
        preferences = student_profile.preferences
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
    
    NOTE: Your Course model should have these fields:
      - career_field
      - required_subjects
      - min_grade
    """
    courses_data = []
    
    for course in courses_queryset.select_related('institution'):
        # Handle JSONField for required_subjects
        required_subjects = course.required_subjects
        if isinstance(required_subjects, str):
            # If it's stored as a string, try to parse it
            import json
            try:
                required_subjects = json.loads(required_subjects)
            except:
                required_subjects = []
        elif required_subjects is None:
            required_subjects = []
            
        courses_data.append({
            'id':                course.id,
            'name':              course.name,
            'career_field':      getattr(course, 'career_field', '') or '',
            'required_subjects': list(required_subjects or []),
            'min_grade':         getattr(course, 'min_grade', 'C') or 'C',
            'institution_id':    course.institution.id,  # Added for diversity
            'institution_name':  course.institution.name,  # Added for logging
        })
    
    print(f"Prepared {len(courses_data)} courses for ML engine")
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


def generate_student_recommendations(user, include_cluster_points=False) -> dict:
    """
    Full ML recommendation pipeline.
    
    Flow:
      1. Get student profile (grades, preferences)
      2. Calculate RIASEC scores from psychometric responses
      3. Fetch all courses and institutions
      4. Run ML engine
      5. Save results to Recommendation model
      6. Return results
    
    Args:
        user: The authenticated user
        include_cluster_points: Whether to calculate and include cluster points
    
    Returns:
        Dictionary with recommendations and optionally cluster points
    """
    from django.apps import apps

    # Get models
    Profile      = apps.get_model('students', 'Profile')
    Course       = apps.get_model('careers', 'Course')
    Institution  = apps.get_model('careers', 'Institution')

    # Get student profile
    try:
        student_profile = user.student_profile
    except Profile.DoesNotExist:
        return {
            "error": "Student profile not found. Please complete your profile first."
        }

    # Calculate RIASEC scores from psychometric test responses
    riasec_scores = calculate_riasec_scores(student_profile)
    
    # Check if student has taken the test
    if not any(riasec_scores.values()):
        return {
            "error": "No psychometric assessment found. Please complete the assessment first."
        }

    # Build student data
    grades_list      = build_grades_list(student_profile)
    preferences_dict = build_preferences_dict(student_profile)

    # Check if grades exist
    if not grades_list:
        return {
            "error": "No grades found. Please enter your KCSE grades first."
        }

    # Calculate cluster points if requested
    cluster_info = {}
    if include_cluster_points:
        try:
            # Import from students app
            from students.utils import calculate_cluster_points
            
            # Calculate points for best cluster (usually cluster 1 for sciences)
            # You could make this dynamic based on student's interests
            cluster_result = calculate_cluster_points(user, cluster_number=1)
            
            if 'error' not in cluster_result:
                cluster_info = {
                    'cluster_points': cluster_result['total_points'],
                    'cluster_message': f"Your cluster points: {cluster_result['total_points']}",
                    'cluster_details': cluster_result
                }
        except ImportError:
            # If students.utils doesn't exist yet, just skip
            print("students.utils not found - skipping cluster calculation")
        except Exception as e:
            print(f"Error calculating cluster points: {e}")

    # Fetch all courses and institutions
    courses      = Course.objects.select_related('institution').all()
    universities = Institution.objects.prefetch_related(
        Prefetch('courses', queryset=Course.objects.all())
    ).all()

    print(f"Found {courses.count()} courses from {universities.count()} institutions")

    courses_data      = get_courses_data(courses)
    universities_data = get_universities_data(universities)

    # Run ML engine with increased top_n for more variety
    engine  = StudentRecommendationEngine()
    results = engine.recommend(
        riasec_scores=riasec_scores,
        grades=grades_list,
        preferences=preferences_dict,
        courses=courses_data,
        universities=universities_data,
        top_courses=20,  # Increased from 10
        top_universities=10,  # Increased from 5
    )

    # Save to RecommendationSession
    session = RecommendationSession.objects.create(
        user=user,
        riasec_categories=results['student_profile']['top_riasec_categories'],
        avg_grade=results['student_profile']['avg_grade'],
        strong_subjects=results['student_profile']['strong_subjects'],
        matched_career_fields=results['student_profile']['matched_career_fields'],
    )

    # Save course recommendations
    institutions_used = set()
    saved_courses = 0
    
    for rec in results['recommended_courses']:
        try:
            course = Course.objects.select_related('institution').get(id=rec['course_id'])
            
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
            institutions_used.add(course.institution.name)
            saved_courses += 1
        except Course.DoesNotExist:
            print(f"Course {rec['course_id']} not found")
            continue

    # Save university recommendations
    for rec in results['recommended_universities']:
        try:
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
        except Institution.DoesNotExist:
            print(f"Institution {rec['university_id']} not found")
            continue

    # Add cluster info to results if available
    if cluster_info:
        results['cluster_info'] = cluster_info

    # Add diversity info to results
    results['diversity_info'] = {
        'total_courses_saved': saved_courses,
        'unique_institutions': len(institutions_used),
        'institutions': list(institutions_used)[:10]  # First 10 institutions
    }

    print(f"Saved {saved_courses} courses from {len(institutions_used)} different institutions")
    return results


def get_student_recommendations_summary(user) -> dict:
    """
    Get a summary of student's recommendations for dashboard display.
    
    Args:
        user: The authenticated user
    
    Returns:
        Dictionary with recommendation summary
    """
    # Get counts
    total_courses = Recommendation.objects.filter(
        user=user, 
        item_type='course'
    ).count()
    
    total_institutions = Recommendation.objects.filter(
        user=user, 
        item_type='institution'
    ).count()
    
    saved_count = Recommendation.objects.filter(
        user=user, 
        is_saved=True
    ).count()
    
    unseen_count = Recommendation.objects.filter(
        user=user, 
        is_seen=False
    ).count()
    
    # Get latest session
    latest_session = RecommendationSession.objects.filter(
        user=user
    ).order_by('-created_at').first()
    
    return {
        'has_recommendations': total_courses > 0 or total_institutions > 0,
        'total_courses': total_courses,
        'total_institutions': total_institutions,
        'saved_count': saved_count,
        'unseen_count': unseen_count,
        'last_generated': latest_session.created_at if latest_session else None,
        'latest_session': {
            'riasec_categories': latest_session.riasec_categories if latest_session else [],
            'avg_grade': latest_session.avg_grade if latest_session else 0,
            'strong_subjects': latest_session.strong_subjects if latest_session else [],
            'matched_career_fields': latest_session.matched_career_fields if latest_session else []
        } if latest_session else None
    }


def regenerate_recommendations(user) -> dict:
    """
    Force regeneration of recommendations (overwrites existing).
    
    Args:
        user: The authenticated user
    
    Returns:
        Dictionary with new recommendations
    """
    # Delete existing recommendations for this user
    Recommendation.objects.filter(user=user).delete()
    RecommendationSession.objects.filter(user=user).delete()
    
    # Generate new ones
    return generate_student_recommendations(user)