from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.db.models import Sum, Avg, Max
from .models import Subject, Cluster, ClusterPointCalculation
from students.models import StudentGrades, Profile  # Import from students app
from .serializers import (
    SubjectSerializer, ClusterSerializer,
    ClusterPointCalculationSerializer
)
from django.contrib.auth.models import User
import logging

logger = logging.getLogger(__name__)


class SubjectViewSet(viewsets.ReadOnlyModelViewSet):
    """List all available subjects"""
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [IsAuthenticated]


class ClusterViewSet(viewsets.ReadOnlyModelViewSet):
    """List all clusters with their subjects"""
    queryset = Cluster.objects.all()
    serializer_class = ClusterSerializer
    permission_classes = [IsAuthenticated]


class ClusterPointCalculationViewSet(viewsets.ModelViewSet):
    """Calculate and view cluster points using students app grades"""
    serializer_class = ClusterPointCalculationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ClusterPointCalculation.objects.filter(user=self.request.user)
    
    def _build_subject_mapping(self):
        """Build comprehensive subject mapping between students app and cluster calculator"""
        subjects = Subject.objects.all()
        
        # Create mapping dictionary
        mapping = {}
        
        # Common KCSE subject codes and variations
        subject_variations = {
            # Compulsory
            'ENGLISH': ['ENGLISH', 'ENG', '101'],
            'KISWAHILI': ['KISWAHILI', 'KISW', 'SWAHILI', '102'],
            'MATHEMATICS': ['MATHEMATICS', 'MATH', 'MATHS', '121'],
            
            # Sciences
            'BIOLOGY': ['BIOLOGY', 'BIO', '231'],
            'CHEMISTRY': ['CHEMISTRY', 'CHEM', '233'],
            'PHYSICS': ['PHYSICS', 'PHY', '232'],
            
            # Humanities
            'HISTORY': ['HISTORY', 'HIST', '311'],
            'GEOGRAPHY': ['GEOGRAPHY', 'GEO', '312'],
            'CRE': ['CRE', 'CHRISTIAN RELIGIOUS EDUCATION', 'CHRISTIAN', '313'],
            'IRE': ['IRE', 'ISLAMIC RELIGIOUS EDUCATION', 'ISLAMIC', '314'],
            'HRE': ['HRE', 'HINDU RELIGIOUS EDUCATION', 'HINDU', '315'],
            
            # Languages
            'FRENCH': ['FRENCH', '501'],
            'GERMAN': ['GERMAN', '502'],
            'ARABIC': ['ARABIC', '503'],
            
            # Technical
            'HOME_SCIENCE': ['HOME SCIENCE', 'HOME_SCIENCE', 'HOMESCIENCE', 'HOME SCI', '511'],
            'AGRICULTURE': ['AGRICULTURE', 'AGRI', '443'],
            'WOODWORK': ['WOODWORK', 'WOOD', '441'],
            'METALWORK': ['METALWORK', 'METAL', '442'],
            'BUILDING_CONSTRUCTION': ['BUILDING CONSTRUCTION', 'BUILDING', 'BUILD', '445'],
            'POWER_MECHANICS': ['POWER MECHANICS', 'POWER', '447'],
            'ELECTRICITY': ['ELECTRICITY', 'ELECT', '448'],
            'DRAWING_DESIGN': ['DRAWING AND DESIGN', 'DRAWING', 'DESIGN', '444'],
            'AVIATION': ['AVIATION TECHNOLOGY', 'AVIATION', '449'],
            'COMPUTER': ['COMPUTER STUDIES', 'COMPUTER', '451'],
            'BUSINESS': ['BUSINESS STUDIES', 'BUSINESS', '565'],
            'MUSIC': ['MUSIC', '521'],
            'ART_DESIGN': ['ART AND DESIGN', 'ART', '522'],
        }
        
        # Build mapping for each subject in cluster calculator
        for subject in subjects:
            subject_key = subject.name.upper()
            subject_code = subject.code.upper() if subject.code else ''
            
            # Store subject by its own name and code
            mapping[subject_key] = subject
            if subject_code:
                mapping[subject_code] = subject
            
            # Check if this subject matches any common variations
            for std_key, variations in subject_variations.items():
                if subject_key in [v.upper() for v in variations] or subject_code in [v.upper() for v in variations]:
                    # Map all variations to this subject
                    for variation in variations:
                        mapping[variation.upper()] = subject
                        # Also map without spaces
                        mapping[variation.upper().replace(' ', '_')] = subject
                        mapping[variation.upper().replace(' ', '')] = subject
        
        return mapping
    
    @action(detail=False, methods=['post'])
    def calculate(self, request):
        """Calculate cluster points based on student's grades from students app"""
        year = request.data.get('year')
        
        if not year:
            return Response({
                'error': 'Year is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get student's profile
            try:
                profile = request.user.student_profile
            except Profile.DoesNotExist:
                return Response({
                    'error': 'Student profile not found. Please create a profile first.'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Get grades from students app
            student_grades = StudentGrades.objects.filter(
                student=profile
            )
            
            if not student_grades.exists():
                return Response({
                    'error': 'No grades found. Please add your KCSE grades first.'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Get subject mapping
            subject_mapping = self._build_subject_mapping()
            
            # Map student grades to cluster calculator subjects
            mapped_grades = []
            unmatched_subjects = []
            
            logger.info(f"Processing {student_grades.count()} grades for user {request.user.username}")
            
            for grade in student_grades:
                subject_code = grade.subject  # This is the subject choice code (e.g., 'CRE', 'HOME_SCIENCE')
                subject_display = grade.get_subject_display().upper()  # Display name (e.g., 'CHRISTIAN RELIGIOUS EDUCATION')
                
                logger.debug(f"Matching grade - Code: {subject_code}, Display: {subject_display}, Grade: {grade.grade}")
                
                # Try to find matching subject in cluster calculator
                matched_subject = None
                
                # Try direct match by code
                if subject_code in subject_mapping:
                    matched_subject = subject_mapping[subject_code]
                    logger.debug(f"Matched by code: {subject_code} -> {matched_subject.name}")
                
                # Try by display name
                elif subject_display in subject_mapping:
                    matched_subject = subject_mapping[subject_display]
                    logger.debug(f"Matched by display: {subject_display} -> {matched_subject.name}")
                
                # Try by code without underscore
                elif subject_code.replace('_', '') in subject_mapping:
                    matched_subject = subject_mapping[subject_code.replace('_', '')]
                    logger.debug(f"Matched by code without underscore: {subject_code} -> {matched_subject.name}")
                
                # Try partial matching
                else:
                    # Look for any mapping key that contains this subject code
                    for key, subj in subject_mapping.items():
                        if subject_code in key or subject_display in key:
                            matched_subject = subj
                            logger.debug(f"Matched by partial: {key} -> {subj.name}")
                            break
                
                if matched_subject:
                    mapped_grades.append({
                        'subject': matched_subject,
                        'subject_obj': matched_subject,
                        'grade_value': grade.grade,
                        'points': grade.points,
                        'original_subject': subject_code,
                        'original_display': subject_display
                    })
                else:
                    unmatched_subjects.append(f"{subject_code} ({subject_display})")
                    logger.warning(f"Unmatched subject: {subject_code} ({subject_display})")
            
            if not mapped_grades:
                return Response({
                    'error': f'Could not match your grades with cluster subjects. Unmatched: {", ".join(unmatched_subjects)}',
                    'debug': {
                        'available_subjects': list(subject_mapping.keys())[:20]  # First 20 for debugging
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
            
            logger.info(f"Successfully mapped {len(mapped_grades)} grades, {len(unmatched_subjects)} unmatched")
            
            # Calculate points for each cluster
            calculations = []
            clusters = Cluster.objects.all().prefetch_related('subjects')
            
            with transaction.atomic():
                # Delete existing calculations for this year
                ClusterPointCalculation.objects.filter(
                    user=request.user, 
                    year=year
                ).delete()
                
                for cluster in clusters:
                    cluster_subject_ids = cluster.subjects.values_list('id', flat=True)
                    
                    # Get grades for subjects in this cluster
                    relevant_grades = [
                        g for g in mapped_grades 
                        if g['subject_obj'].id in cluster_subject_ids
                    ]
                    
                    if len(relevant_grades) >= 4:
                        # Sort by points and take top 4
                        top_grades = sorted(relevant_grades, key=lambda x: x['points'], reverse=True)[:4]
                        
                        total_points = sum(g['points'] for g in top_grades)
                        subjects_used = [
                            {
                                'subject': g['subject_obj'].name,
                                'grade': g['grade_value'],
                                'points': g['points'],
                                'original_subject': g['original_subject']
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
                        logger.info(f"Created calculation for {cluster.name}: {total_points} points")
            
            # Prepare response
            serializer = self.get_serializer(calculations, many=True)
            
            response_data = {
                'status': 'success',
                'message': f'Calculated points for {len(calculations)} clusters',
                'data': serializer.data,
                'debug': {
                    'total_grades': student_grades.count(),
                    'mapped_grades': len(mapped_grades),
                    'unmatched_subjects': unmatched_subjects
                }
            }
            
            if unmatched_subjects:
                response_data['warning'] = f"Could not match these subjects: {', '.join(unmatched_subjects)}"
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error calculating cluster points: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Get latest cluster calculations with grades summary"""
        year = request.query_params.get('year')
        
        if year:
            calculations = ClusterPointCalculation.objects.filter(
                user=request.user,
                year=year
            )
        else:
            # Get latest year with calculations
            latest_year = ClusterPointCalculation.objects.filter(
                user=request.user
            ).order_by('-year').values_list('year', flat=True).first()
            
            if latest_year:
                calculations = ClusterPointCalculation.objects.filter(
                    user=request.user,
                    year=latest_year
                )
            else:
                calculations = ClusterPointCalculation.objects.none()
        
        serializer = self.get_serializer(calculations, many=True)
        
        # Get grades summary from students app
        try:
            profile = request.user.student_profile
            grades = StudentGrades.objects.filter(student=profile)
            grades_summary = [
                {
                    'subject': g.get_subject_display(),
                    'subject_code': g.subject,
                    'grade': g.grade,
                    'points': g.points
                } for g in grades
            ]
        except:
            grades_summary = []
        
        return Response({
            'status': 'success',
            'calculations': serializer.data,
            'grades_summary': grades_summary,
            'has_grades': len(grades_summary) > 0
        })
    
    @action(detail=False, methods=['post'])
    def debug_grades(self, request):
        """Debug endpoint to see what grades are available and how they map"""
        try:
            profile = request.user.student_profile
            grades = StudentGrades.objects.filter(student=profile)
            
            grades_data = []
            for g in grades:
                grades_data.append({
                    'id': g.id,
                    'subject_code': g.subject,
                    'subject_display': g.get_subject_display(),
                    'grade': g.grade,
                    'points': g.points
                })
            
            # Get cluster subjects for comparison
            clusters_data = []
            subjects_data = []
            
            for c in Cluster.objects.all():
                clusters_data.append({
                    'cluster': c.name,
                    'code': c.code,
                    'subjects': [{'id': s.id, 'name': s.name, 'code': s.code} for s in c.subjects.all()]
                })
            
            for s in Subject.objects.all():
                subjects_data.append({
                    'id': s.id,
                    'name': s.name,
                    'code': s.code,
                    'is_compulsory': s.is_compulsory
                })
            
            # Show mapping
            subject_mapping = self._build_subject_mapping()
            mapping_preview = {k: v.name for k, v in list(subject_mapping.items())[:20]}
            
            return Response({
                'status': 'success',
                'grades': grades_data,
                'grades_count': len(grades_data),
                'clusters': clusters_data,
                'subjects': subjects_data,
                'subjects_count': len(subjects_data),
                'mapping_preview': mapping_preview
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'error': str(e)
            })