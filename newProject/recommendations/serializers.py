from rest_framework import serializers
from .models import Recommendation, RecommendationSession


class RecommendationSerializer(serializers.ModelSerializer):
    """Serializer for a single recommendation."""

    class Meta:
        model = Recommendation
        fields = [
            'id',
            'item_id',
            'item_type',
            'item_name',
            'score',
            'recommendation_type',
            'match_reasons',
            'is_seen',
            'is_saved',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'item_id',
            'item_type',
            'item_name',
            'score',
            'recommendation_type',
            'match_reasons',
            'created_at',
        ]


class RecommendationSessionSerializer(serializers.ModelSerializer):
    """Serializer for a recommendation session (student profile snapshot)."""

    class Meta:
        model = RecommendationSession
        fields = [
            'id',
            'riasec_categories',
            'avg_grade',
            'strong_subjects',
            'matched_career_fields',
            'created_at',
        ]
        read_only_fields = fields


class RecommendationResultSerializer(serializers.Serializer):
    """
    Serializer for the full ML engine output returned after
    POST /api/recommendations/generate/
    """

    class StudentProfileSerializer(serializers.Serializer):
        top_riasec_categories = serializers.ListField(
            child=serializers.CharField()
        )
        avg_grade = serializers.FloatField()
        strong_subjects = serializers.ListField(
            child=serializers.CharField()
        )
        matched_career_fields = serializers.ListField(
            child=serializers.CharField()
        )

    class RecommendedCourseSerializer(serializers.Serializer):
        course_id = serializers.IntegerField()
        course_name = serializers.CharField()
        score = serializers.FloatField()
        match_reasons = serializers.ListField(
            child=serializers.CharField()
        )

    class RecommendedUniversitySerializer(serializers.Serializer):
        university_id = serializers.IntegerField()
        university_name = serializers.CharField()
        score = serializers.FloatField()
        match_reasons = serializers.ListField(
            child=serializers.CharField()
        )

    student_profile = StudentProfileSerializer()
    recommended_courses = RecommendedCourseSerializer(many=True)
    recommended_universities = RecommendedUniversitySerializer(many=True)


class MarkSeenSerializer(serializers.Serializer):
    """Serializer for marking a recommendation as seen."""
    is_seen = serializers.BooleanField()


class MarkSavedSerializer(serializers.Serializer):
    """Serializer for bookmarking/unbookmarking a recommendation."""
    is_saved = serializers.BooleanField()