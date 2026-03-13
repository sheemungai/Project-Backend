from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Recommendation, RecommendationSession
from .serializers import (
    RecommendationSerializer,
    EnhancedRecommendationSerializer,
    RecommendationSessionSerializer,
    RecommendationResultSerializer,
    CourseDetailSerializer,
    MarkSeenSerializer,
    MarkSavedSerializer,
)
from .services import generate_student_recommendations


# ─────────────────────────────────────────────────────────────────────────────
# 1. GENERATE RECOMMENDATIONS
# ─────────────────────────────────────────────────────────────────────────────

class GenerateRecommendationsView(APIView):
    """
    Triggers the ML engine to generate recommendations for the
    authenticated student.

    Called after the student completes the psychometric test.

    POST /api/recommendations/generate/

    Returns:
    {
        "student_profile": {
            "top_riasec_categories": [...],
            "avg_grade": 9.5,
            "strong_subjects": [...],
            "matched_career_fields": [...]
        },
        "recommended_courses": [
            {
                "course_id": 1,
                "course_name": "Computer Science",
                "score": 0.85,
                "match_reasons": [...]
            }, ...
        ],
        "recommended_universities": [
            {
                "university_id": 1,
                "university_name": "University of Nairobi",
                "score": 0.75,
                "match_reasons": [...]
            }, ...
        ]
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        results = generate_student_recommendations(user=request.user)

        # Return error if assessment not found
        if 'error' in results:
            return Response(results, status=status.HTTP_400_BAD_REQUEST)

        serializer = RecommendationResultSerializer(results)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────────────────────────────────────
# 2. RECOMMENDATIONS VIEWSET
# ─────────────────────────────────────────────────────────────────────────────

class RecommendationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Endpoints for viewing and managing student recommendations.

    GET  /api/recommendations/                    → all recommendations
    GET  /api/recommendations/?item_type=course   → courses only
    GET  /api/recommendations/?item_type=institution → institutions only
    GET  /api/recommendations/?is_saved=true      → saved/bookmarked only
    GET  /api/recommendations/{id}/               → single recommendation
    GET  /api/recommendations/detailed/           → enhanced with career paths
    GET  /api/recommendations/{id}/course-details/→ detailed course info
    POST /api/recommendations/{id}/mark_seen/     → mark as seen
    POST /api/recommendations/{id}/mark_saved/    → bookmark/unbookmark
    GET  /api/recommendations/courses/            → shortcut for courses
    GET  /api/recommendations/institutions/       → shortcut for institutions
    GET  /api/recommendations/saved/              → shortcut for saved items
    """
    serializer_class = RecommendationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Returns recommendations for the logged-in student.
        Supports filtering by:
          - item_type: 'course' or 'institution'
          - is_saved:  'true' or 'false'
          - is_seen:   'true' or 'false'
        """
        queryset = Recommendation.objects.filter(
            user=self.request.user
        ).order_by('-score', '-created_at')

        # Filter by item type
        item_type = self.request.query_params.get('item_type')
        if item_type in ['course', 'institution']:
            queryset = queryset.filter(item_type=item_type)

        # Filter by saved status
        is_saved = self.request.query_params.get('is_saved')
        if is_saved is not None:
            queryset = queryset.filter(is_saved=is_saved.lower() == 'true')

        # Filter by seen status
        is_seen = self.request.query_params.get('is_seen')
        if is_seen is not None:
            queryset = queryset.filter(is_seen=is_seen.lower() == 'true')

        return queryset

    # ── GET /api/recommendations/detailed/ ──
    @action(detail=False, methods=['get'], url_path='detailed')
    def detailed(self, request):
        """Get recommendations with career paths and detailed info"""
        queryset = self.get_queryset()
        serializer = EnhancedRecommendationSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    # ── GET /api/recommendations/{id}/course-details/ ──
    @action(detail=True, methods=['get'], url_path='course-details')
    def course_details(self, request, pk=None):
        """Get detailed course information for a recommendation"""
        recommendation = self.get_object()
        
        if recommendation.item_type != 'course':
            return Response(
                {"error": "This recommendation is not a course"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from careers.models import Course
            course = Course.objects.get(id=recommendation.item_id)
            serializer = CourseDetailSerializer(course)
            return Response(serializer.data)
        except Course.DoesNotExist:
            return Response(
                {"error": "Course not found"},
                status=status.HTTP_404_NOT_FOUND
            )

    # ── POST /api/recommendations/{id}/mark_seen/ ──
    @action(detail=True, methods=['post'], url_path='mark_seen')
    def mark_seen(self, request, pk=None):
        """Mark a recommendation as seen."""
        recommendation = self.get_object()
        serializer = MarkSeenSerializer(data=request.data)

        if serializer.is_valid():
            recommendation.is_seen = serializer.validated_data['is_seen']
            recommendation.save()
            return Response(
                {
                    "detail": "Updated successfully.",
                    "is_seen": recommendation.is_seen
                },
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # ── POST /api/recommendations/{id}/mark_saved/ ──
    @action(detail=True, methods=['post'], url_path='mark_saved')
    def mark_saved(self, request, pk=None):
        """Bookmark or unbookmark a recommendation."""
        recommendation = self.get_object()
        serializer = MarkSavedSerializer(data=request.data)

        if serializer.is_valid():
            recommendation.is_saved = serializer.validated_data['is_saved']
            recommendation.save()
            return Response(
                {
                    "detail": "Updated successfully.",
                    "is_saved": recommendation.is_saved
                },
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # ── GET /api/recommendations/courses/ ──
    @action(detail=False, methods=['get'], url_path='courses')
    def courses(self, request):
        """Shortcut to get only course recommendations."""
        queryset = self.get_queryset().filter(item_type='course')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    # ── GET /api/recommendations/institutions/ ──
    @action(detail=False, methods=['get'], url_path='institutions')
    def institutions(self, request):
        """Shortcut to get only institution recommendations."""
        queryset = self.get_queryset().filter(item_type='institution')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    # ── GET /api/recommendations/saved/ ──
    @action(detail=False, methods=['get'], url_path='saved')
    def saved(self, request):
        """Get all bookmarked recommendations."""
        queryset = self.get_queryset().filter(is_saved=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


# ─────────────────────────────────────────────────────────────────────────────
# 3. RECOMMENDATION STATUS VIEW
# ─────────────────────────────────────────────────────────────────────────────

class RecommendationStatusView(APIView):
    """
    Check if recommendations exist for the current user.
    
    GET /api/recommendations/status/
    
    Returns:
    {
        "exists": true/false,
        "lastGenerated": "2024-01-15T10:30:00Z",
        "count": 15
    }
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        count = Recommendation.objects.filter(user=request.user).count()
        latest = RecommendationSession.objects.filter(user=request.user).first()
        
        return Response({
            "exists": count > 0,
            "lastGenerated": latest.created_at.isoformat() if latest else None,
            "count": count
        })


# ─────────────────────────────────────────────────────────────────────────────
# 4. RECOMMENDATION SESSION VIEWSET
# ─────────────────────────────────────────────────────────────────────────────

class RecommendationSessionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Endpoints for viewing recommendation session history
    (each time the ML engine ran for this student).

    GET /api/recommendations/sessions/         → all sessions
    GET /api/recommendations/sessions/{id}/    → single session
    GET /api/recommendations/sessions/latest/  → most recent session
    """
    serializer_class = RecommendationSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return RecommendationSession.objects.filter(
            user=self.request.user
        ).order_by('-created_at')

    # ── GET /api/recommendations/sessions/latest/ ──
    @action(detail=False, methods=['get'], url_path='latest')
    def latest(self, request):
        """Get the most recent recommendation session."""
        session = self.get_queryset().first()

        if not session:
            return Response(
                {"detail": "No recommendation sessions found. "
                           "Please complete the psychometric test first."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(session)
        return Response(serializer.data)