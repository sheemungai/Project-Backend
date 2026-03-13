from rest_framework import serializers
from .models import Recommendation, RecommendationSession
from careers.models import CareerPath, Course


class CareerPathSerializer(serializers.ModelSerializer):
    """Serializer for career paths"""
    class Meta:
        model = CareerPath
        fields = [
            'id',
            'name',
            'description',
            'required_skills',
            'average_salary',
        ]


class CourseDetailSerializer(serializers.ModelSerializer):
    """Detailed course serializer with career paths"""
    institution_name = serializers.CharField(source='institution.name')
    institution_location = serializers.CharField(source='institution.location')
    career_paths = CareerPathSerializer(many=True, read_only=True)
    
    class Meta:
        model = Course
        fields = [
            'id',
            'name',
            'prog_code',
            'institution_name',
            'institution_location',
            'career_field',
            'career_paths',
            'required_subjects',
            'min_grade',
            'cutoff_2022',
            'cutoff_2023',
            'cutoff_2024',
            'cutoff_2025',
        ]


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


class EnhancedRecommendationSerializer(serializers.ModelSerializer):
    """Enhanced recommendation serializer with career paths"""
    career_paths = serializers.SerializerMethodField()
    institution_name = serializers.SerializerMethodField()
    institution_location = serializers.SerializerMethodField()
    match_reasons_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Recommendation
        fields = [
            'id',
            'item_id',
            'item_type',
            'item_name',
            'institution_name',
            'institution_location',
            'score',
            'recommendation_type',
            'match_reasons',
            'match_reasons_display',
            'career_paths',
            'is_seen',
            'is_saved',
            'created_at',
        ]
    
    def get_career_paths(self, obj):
        """Get career paths for courses"""
        if obj.item_type == 'course':
            try:
                from careers.models import Course
                course = Course.objects.get(id=obj.item_id)
                paths = course.career_paths.all()
                return CareerPathSerializer(paths, many=True).data
            except Course.DoesNotExist:
                return []
        return []
    
    def get_institution_name(self, obj):
        """Get institution name for courses"""
        if obj.item_type == 'course':
            try:
                from careers.models import Course
                course = Course.objects.get(id=obj.item_id)
                return course.institution.name
            except Course.DoesNotExist:
                return None
        return obj.item_name
    
    def get_institution_location(self, obj):
        """Get institution location for courses"""
        if obj.item_type == 'course':
            try:
                from careers.models import Course
                course = Course.objects.get(id=obj.item_id)
                return course.institution.location
            except Course.DoesNotExist:
                return None
        return None
    
    def get_match_reasons_display(self, obj):
        """Format match reasons for better display"""
        reasons = obj.match_reasons
        
        # Categorize reasons
        categorized = {
            'personality': [],
            'academic': [],
            'preferences': [],
            'career': [],
            'other': []
        }
        
        for reason in reasons:
            reason_lower = reason.lower()
            if 'personality' in reason_lower or 'riasec' in reason_lower or 'type' in reason_lower:
                categorized['personality'].append(reason)
            elif 'grade' in reason_lower or 'subject' in reason_lower or 'strong' in reason_lower or 'meet' in reason_lower:
                categorized['academic'].append(reason)
            elif 'prefer' in reason_lower or 'interest' in reason_lower or 'stated' in reason_lower:
                categorized['preferences'].append(reason)
            elif 'career' in reason_lower or 'field' in reason_lower or 'path' in reason_lower:
                categorized['career'].append(reason)
            else:
                categorized['other'].append(reason)
        
        return categorized


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