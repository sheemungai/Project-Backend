from rest_framework import serializers
from .models import Subject, Grade, Cluster, StudentGrade, ClusterPointCalculation


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id', 'name', 'code', 'is_compulsory', 'created_at']


class GradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = ['id', 'grade', 'points']


class ClusterSerializer(serializers.ModelSerializer):
    subjects = SubjectSerializer(many=True, read_only=True)
    
    class Meta:
        model = Cluster
        fields = ['id', 'name', 'code', 'description', 'subjects', 'created_at']


class StudentGradeSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    grade_value = serializers.CharField(source='grade.grade', read_only=True)
    points = serializers.IntegerField(source='grade.points', read_only=True)
    
    class Meta:
        model = StudentGrade
        fields = ['id', 'user', 'subject', 'subject_name', 'grade', 'grade_value', 
                  'points', 'year', 'created_at', 'updated_at']
        read_only_fields = ['user', 'created_at', 'updated_at']


class StudentGradeInputSerializer(serializers.Serializer):
    """For batch input of student grades"""
    subject_id = serializers.IntegerField()
    grade_id = serializers.IntegerField()


class CalculateClusterPointsSerializer(serializers.Serializer):
    """Input for calculating cluster points"""
    grades = StudentGradeInputSerializer(many=True)
    year = serializers.IntegerField()


class ClusterPointCalculationSerializer(serializers.ModelSerializer):
    cluster_name = serializers.CharField(source='cluster.name', read_only=True)
    cluster_code = serializers.CharField(source='cluster.code', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = ClusterPointCalculation
        fields = ['id', 'user', 'username', 'cluster', 'cluster_name', 'cluster_code',
                  'total_points', 'subjects_used', 'year', 'created_at']
        read_only_fields = ['user', 'created_at']