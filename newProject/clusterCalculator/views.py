from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from .models import Subject, Grade, Cluster, StudentGrade, ClusterPointCalculation
from .serializers import (
    SubjectSerializer, GradeSerializer, ClusterSerializer,
    StudentGradeSerializer, CalculateClusterPointsSerializer,
    ClusterPointCalculationSerializer
)


class SubjectViewSet(viewsets.ReadOnlyModelViewSet):
    """List all available subjects"""
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [IsAuthenticated]


class GradeViewSet(viewsets.ReadOnlyModelViewSet):
    """List all available grades"""
    queryset = Grade.objects.all()
    serializer_class = GradeSerializer
    permission_classes = [IsAuthenticated]


class ClusterViewSet(viewsets.ReadOnlyModelViewSet):
    """List all clusters with their subjects"""
    queryset = Cluster.objects.all()
    serializer_class = ClusterSerializer
    permission_classes = [IsAuthenticated]


class StudentGradeViewSet(viewsets.ModelViewSet):
    """Manage student grades"""
    serializer_class = StudentGradeSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return StudentGrade.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def batch_create(self, request):
        """Create multiple grades at once"""
        serializer = CalculateClusterPointsSerializer(data=request.data)
        if serializer.is_valid():
            grades_data = serializer.validated_data['grades']
            year = serializer.validated_data['year']
            
            created_grades = []
            with transaction.atomic():
                # Delete existing grades for this year
                StudentGrade.objects.filter(user=request.user, year=year).delete()
                
                for grade_data in grades_data:
                    student_grade = StudentGrade.objects.create(
                        user=request.user,
                        subject_id=grade_data['subject_id'],
                        grade_id=grade_data['grade_id'],
                        year=year
                    )
                    created_grades.append(student_grade)
            
            output_serializer = StudentGradeSerializer(created_grades, many=True)
            return Response({
                'status': 'success',
                'message': f'{len(created_grades)} grades saved successfully',
                'data': output_serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ClusterPointCalculationViewSet(viewsets.ModelViewSet):
    """Calculate and view cluster points"""
    serializer_class = ClusterPointCalculationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ClusterPointCalculation.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def calculate(self, request):
        """Calculate cluster points for all clusters based on student's grades"""
        year = request.data.get('year')
        
        if not year:
            return Response({
                'error': 'Year is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get student's grades for the specified year
        student_grades = StudentGrade.objects.filter(
            user=request.user,
            year=year
        ).select_related('subject', 'grade')
        
        if not student_grades.exists():
            return Response({
                'error': 'No grades found for the specified year'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Calculate points for each cluster
        calculations = []
        clusters = Cluster.objects.all().prefetch_related('subjects')
        
        with transaction.atomic():
            # Delete existing calculations for this year
            ClusterPointCalculation.objects.filter(user=request.user, year=year).delete()
            
            for cluster in clusters:
                cluster_subject_ids = cluster.subjects.values_list('id', flat=True)
                
                # Get grades for subjects in this cluster
                relevant_grades = student_grades.filter(subject_id__in=cluster_subject_ids)
                
                if relevant_grades.count() >= 4:
                    # Sort by points and take top 4 (including compulsory subjects if any)
                    top_grades = sorted(relevant_grades, key=lambda x: x.grade.points, reverse=True)[:4]
                    
                    total_points = sum(g.grade.points for g in top_grades)
                    subjects_used = [
                        {
                            'subject': g.subject.name,
                            'grade': g.grade.grade,
                            'points': g.grade.points
                        } for g in top_grades
                    ]
                    
                    calculation = ClusterPointCalculation.objects.create(
                        user=request.user,
                        cluster=cluster,
                        total_points=total_points,
                        subjects_used=subjects_used,
                        year=year
                    )
                    calculations.append(calculation)
        
        serializer = ClusterPointCalculationSerializer(calculations, many=True)
        return Response({
            'status': 'success',
            'message': f'Calculated points for {len(calculations)} clusters',
            'data': serializer.data
        }, status=status.HTTP_200_OK)