from unicodedata import name
from django.db import models

# Create your models here.
class Institution(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100) 
    type = models.CharField(max_length=50, choices=[('PUBLIC', 'Public'), ('PRIVATE', 'Private')],  default="PUBLIC", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']


class Course(models.Model):
    prog_code = models.CharField(max_length=20, unique=True)  
    name = models.CharField(max_length=255)
    institution = models.ForeignKey(Institution, related_name='courses', on_delete=models.CASCADE)
    
    # ── ML Recommendation Fields (ADD THESE) ──
    career_field = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="e.g., Engineering, Medicine, Computer Science, Business"
    )
    required_subjects = models.JSONField(
        default=list,
        blank=True,
        help_text="e.g., ['MATHEMATICS', 'PHYSICS', 'CHEMISTRY']"
    )
    min_grade = models.CharField(
        max_length=2,
        default='C',
        choices=[
            ('A', 'A'), ('A-', 'A-'), ('B+', 'B+'), ('B', 'B'),
            ('B-', 'B-'), ('C+', 'C+'), ('C', 'C'), ('C-', 'C-'),
            ('D+', 'D+'), ('D', 'D'), ('D-', 'D-'), ('E', 'E'),
        ],
        help_text="Minimum mean grade required for admission"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Cut-off points by year
    cutoff_2018 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    cutoff_2019 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    cutoff_2020 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    cutoff_2021 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    cutoff_2022 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    cutoff_2023 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    cutoff_2024 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    cutoff_2025 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.institution.name}"
    
    class Meta:
        ordering = ['institution__name', 'name']


class CareerPath(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    required_skills = models.TextField()
    average_salary = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    related_courses = models.ManyToManyField(Course, related_name='career_paths', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name