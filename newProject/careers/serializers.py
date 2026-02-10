from rest_framework import serializers
from .models import CareerPath, Course, Institution


class CareerPathSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareerPath
        fields = '__all__'


class CourseSerializer(serializers.ModelSerializer):
    career_paths = CareerPathSerializer(many=True, read_only=True)
    career_path_ids = serializers.PrimaryKeyRelatedField(
        many=True, 
        queryset=CareerPath.objects.all(), 
        source='career_paths',
        write_only=True
    )
    
    class Meta:
        model = Course
        fields = '__all__'


class InstitutionSerializer(serializers.ModelSerializer):
    courses = CourseSerializer(many=True, read_only=True)
    course_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Course.objects.all(),
        source='courses',
        write_only=True
    )
    
    class Meta:
        model = Institution
        fields = '__all__'