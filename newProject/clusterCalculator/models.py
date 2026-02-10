from django.db import models
from django.contrib.auth.models import User


class Subject(models.Model):
    """KCSE Subjects"""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)  # e.g., '121' for Math
    is_compulsory = models.BooleanField(default=False)  # Math, English, Kiswahili
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']


class Grade(models.Model):
    """KCSE Grading system"""
    GRADE_CHOICES = [
        ('A', 'A'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B', 'B'),
        ('B-', 'B-'),
        ('C+', 'C+'),
        ('C', 'C'),
        ('C-', 'C-'),
        ('D+', 'D+'),
        ('D', 'D'),
        ('D-', 'D-'),
        ('E', 'E'),
    ]
    
    grade = models.CharField(max_length=2, choices=GRADE_CHOICES, unique=True)
    points = models.IntegerField()
    
    def __str__(self):
        return f"{self.grade} - {self.points} points"
    
    class Meta:
        ordering = ['-points']


class Cluster(models.Model):
    """Career clusters (e.g., Science, Arts, Technical)"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)  # e.g., 'CLUSTER_1'
    description = models.TextField()
    subjects = models.ManyToManyField(Subject, related_name='clusters')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    class Meta:
        ordering = ['code']


class StudentGrade(models.Model):
    """Store student's KCSE grades"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='kcse_grades')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE)
    year = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.subject.name}: {self.grade.grade}"
    
    class Meta:
        unique_together = ['user', 'subject', 'year']
        ordering = ['-created_at']


class ClusterPointCalculation(models.Model):
    """Store calculated cluster points for students"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cluster_calculations')
    cluster = models.ForeignKey(Cluster, on_delete=models.CASCADE)
    total_points = models.DecimalField(max_digits=5, decimal_places=2)
    subjects_used = models.JSONField()  # Store which subjects were used in calculation
    year = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.cluster.code}: {self.total_points} points"
    
    class Meta:
        unique_together = ['user', 'cluster', 'year']
        ordering = ['-total_points']