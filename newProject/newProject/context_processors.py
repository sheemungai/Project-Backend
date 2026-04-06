# Backend/newProject/context_processors.py
from django.contrib.auth.models import User
from assessment.models import PsychometricResponse
from recommendations.models import Recommendation
from careers.models import CareerPath

def admin_stats(request):
    """Add statistics to admin template context"""
    if not request.user.is_staff:
        return {}
    
    # Get unique students who completed assessment
    completed_assessments = PsychometricResponse.objects.values('student').distinct().count()
    
    return {
        'total_students': User.objects.filter(is_staff=False).count(),
        'completed_assessments': completed_assessments,
        'total_recommendations': Recommendation.objects.count(),
        'total_careers': CareerPath.objects.count(),
    }