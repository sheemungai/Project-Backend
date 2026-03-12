from rest_framework import serializers
from .models import CareerPath, Course, Institution


class InstitutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institution
        fields = ['id', 'name', 'location', 'type']


class SimpleCourseSerializer(serializers.ModelSerializer):
    institution = InstitutionSerializer(read_only=True)
    
    class Meta:
        model = Course
        fields = ['id', 'name', 'prog_code', 'cutoff_2024', 'institution']


class CareerPathSerializer(serializers.ModelSerializer):
    related_courses = SimpleCourseSerializer(many=True, read_only=True)
    
    class Meta:
        model = CareerPath
        fields = '__all__'


class CourseSerializer(serializers.ModelSerializer):
    career_paths = CareerPathSerializer(many=True, read_only=True)
    institution = InstitutionSerializer(read_only=True)
    career_path_ids = serializers.PrimaryKeyRelatedField(
        many=True, 
        queryset=CareerPath.objects.all(), 
        source='career_paths',
        write_only=True
    )
    institution_id = serializers.PrimaryKeyRelatedField(
        queryset=Institution.objects.all(),
        source='institution',
        write_only=True
    )
    
    class Meta:
        model = Course
        fields = '__all__'


class InstitutionDetailSerializer(serializers.ModelSerializer):
    courses = SimpleCourseSerializer(many=True, read_only=True)
    
    class Meta:
        model = Institution
        fields = '__all__'