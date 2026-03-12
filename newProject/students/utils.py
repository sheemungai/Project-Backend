# students/utils.py
"""
Utility functions for grade calculations including cluster points.
Create this file at: your_project/students/utils.py
"""

from collections import defaultdict
from typing import Dict, List, Optional, Union

# KCSE subject clusters mapping (Kenya system)
CLUSTER_SUBJECTS = {
    1: ['MATHEMATICS', 'PHYSICS', 'CHEMISTRY', 'BIOLOGY'],  # Cluster 1: Sciences
    2: ['MATHEMATICS', 'PHYSICS', 'CHEMISTRY', 'GEOGRAPHY'],  # Cluster 2: Physical Sciences
    3: ['ENGLISH', 'KISWAHILI', 'HISTORY', 'GEOGRAPHY'],  # Cluster 3: Humanities
    4: ['MATHEMATICS', 'BUSINESS', 'ECONOMICS', 'COMMERCE'],  # Cluster 4: Business
    5: ['ENGLISH', 'LITERATURE', 'HISTORY', 'CRE'],  # Cluster 5: Languages & Arts
    6: ['BIOLOGY', 'CHEMISTRY', 'AGRICULTURE', 'HOME SCIENCE'],  # Cluster 6: Applied Sciences
}

# Grade to points mapping
GRADE_TO_POINTS = {
    'A': 12, 'A-': 11, 'B+': 10, 'B': 9, 'B-': 8,
    'C+': 7, 'C': 6, 'C-': 5, 'D+': 4, 'D': 3, 'D-': 2, 'E': 1
}

# Points to grade mapping (for reverse lookup)
POINTS_TO_GRADE = {v: k for k, v in GRADE_TO_POINTS.items()}


def calculate_cluster_points(user, cluster_number: int = 1) -> Dict:
    """
    Calculate cluster points for a specific cluster.
    
    Args:
        user: The authenticated user
        cluster_number: The cluster number (1-6, defaults to 1 for Sciences)
    
    Returns:
        Dictionary with cluster points calculation results
        
    Example:
        >>> calculate_cluster_points(user, cluster_number=1)
        {
            'total_points': 42,
            'subjects': {
                'MATHEMATICS': {'grade': 'A', 'points': 12},
                'PHYSICS': {'grade': 'A-', 'points': 11},
                'CHEMISTRY': {'grade': 'B+', 'points': 10},
                'BIOLOGY': {'grade': 'B', 'points': 9}
            },
            'cluster': 1,
            'cluster_name': 'Cluster 1',
            'mean_grade': 'B+',
            'subject_count': 4,
            'missing_subjects': [],
            'is_complete': True
        }
    """
    from django.apps import apps
    
    try:
        # Get the student's profile and grades
        Profile = apps.get_model('students', 'Profile')
        Grade = apps.get_model('students', 'Grade')  # Assuming Grade model is in students app
        
        # Get student profile
        try:
            profile = user.student_profile
        except Profile.DoesNotExist:
            return {
                'error': 'Student profile not found',
                'total_points': 0,
                'subjects': {}
            }
        
        # Get all grades for this student
        grades = Grade.objects.filter(profile=profile)
        
        if not grades.exists():
            return {
                'error': 'No grades found',
                'total_points': 0,
                'subjects': {}
            }
        
        # Get subjects for the specified cluster
        cluster_subjects = CLUSTER_SUBJECTS.get(cluster_number, [])
        
        if not cluster_subjects:
            return {
                'error': f'Invalid cluster number: {cluster_number}',
                'total_points': 0,
                'subjects': {}
            }
        
        # Find grades for cluster subjects
        subject_grades = {}
        found_subjects = []
        
        for grade in grades:
            if grade.subject in cluster_subjects:
                points = GRADE_TO_POINTS.get(grade.grade, 0)
                subject_grades[grade.subject] = {
                    'grade': grade.grade,
                    'points': points
                }
                found_subjects.append(grade.subject)
        
        # Calculate total points
        total_points = sum(data['points'] for data in subject_grades.values())
        
        # Calculate mean grade
        if len(subject_grades) > 0:
            mean_points = total_points / len(subject_grades)
            # Round to nearest grade
            mean_grade = POINTS_TO_GRADE.get(round(mean_points), 'C')
        else:
            mean_grade = 'N/A'
        
        return {
            'total_points': total_points,
            'subjects': subject_grades,
            'cluster': cluster_number,
            'cluster_name': f'Cluster {cluster_number}',
            'mean_grade': mean_grade,
            'subject_count': len(subject_grades),
            'missing_subjects': [s for s in cluster_subjects if s not in found_subjects],
            'is_complete': len(subject_grades) == 4  # Complete cluster has 4 subjects
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'total_points': 0,
            'subjects': {}
        }


def calculate_all_clusters(user) -> Dict:
    """
    Calculate points for all clusters (1-6).
    
    Args:
        user: The authenticated user
    
    Returns:
        Dictionary with points for all clusters
    """
    results = {}
    
    for cluster_num in range(1, 7):  # Clusters 1-6
        results[cluster_num] = calculate_cluster_points(user, cluster_num)
    
    # Find the best performing cluster
    best_cluster = max(
        results.items(),
        key=lambda x: x[1].get('total_points', 0) if 'error' not in x[1] else 0
    )
    
    return {
        'clusters': results,
        'best_cluster': {
            'cluster': best_cluster[0],
            'points': best_cluster[1].get('total_points', 0),
            'mean_grade': best_cluster[1].get('mean_grade', 'N/A')
        }
    }


def calculate_mean_grade(grades_queryset) -> Dict:
    """
    Calculate mean grade from a queryset of Grade objects.
    
    Args:
        grades_queryset: Django queryset of Grade objects
    
    Returns:
        Dictionary with mean grade information
    """
    if not grades_queryset.exists():
        return {
            'mean_points': 0,
            'mean_grade': 'N/A',
            'total_points': 0,
            'subject_count': 0
        }
    
    total_points = 0
    subject_count = grades_queryset.count()
    
    for grade in grades_queryset:
        points = GRADE_TO_POINTS.get(grade.grade, 0)
        total_points += points
    
    mean_points = total_points / subject_count if subject_count > 0 else 0
    
    # Find closest grade
    closest_points = min(POINTS_TO_GRADE.keys(), key=lambda x: abs(x - mean_points))
    mean_grade = POINTS_TO_GRADE.get(closest_points, 'C')
    
    return {
        'mean_points': round(mean_points, 2),
        'mean_grade': mean_grade,
        'total_points': total_points,
        'subject_count': subject_count
    }


def get_strong_subjects(grades_queryset, threshold: str = 'B+') -> List[str]:
    """
    Get subjects with grades above a certain threshold.
    
    Args:
        grades_queryset: Django queryset of Grade objects
        threshold: Minimum grade (default: 'B+')
    
    Returns:
        List of strong subjects
    """
    threshold_points = GRADE_TO_POINTS.get(threshold, 10)  # B+ = 10 points
    
    strong_subjects = []
    for grade in grades_queryset:
        points = GRADE_TO_POINTS.get(grade.grade, 0)
        if points >= threshold_points:
            strong_subjects.append(grade.subject)
    
    return strong_subjects


def format_grades_for_ml(grades_queryset) -> List[Dict]:
    """
    Format grades for the ML engine.
    
    Args:
        grades_queryset: Django queryset of Grade objects
    
    Returns:
        List of dicts with 'subject' and 'grade' keys
    """
    return [
        {
            'subject': grade.subject,
            'grade': grade.grade
        }
        for grade in grades_queryset
    ]