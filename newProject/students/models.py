from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile', null=True, blank=True)
    address = models.TextField()
    dob = models.DateField()
    gender = models.CharField(max_length=50)
    phone = models.CharField(max_length=20)
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username
    
class StudentGrades(models.Model):
    GRADE_CHOICES = [
       ('A', 'A - 12 points'),
        ('A-', 'A- - 11 points'),
        ('B+', 'B+ - 10 points'),
        ('B', 'B - 9 points'),
        ('B-', 'B- - 8 points'),
        ('C+', 'C+ - 7 points'),
        ('C', 'C - 6 points'),
        ('C-', 'C- - 5 points'),
        ('D+', 'D+ - 4 points'),
        ('D', 'D - 3 points'),
        ('D-', 'D- - 2 points'),
        ('E', 'E - 1 point'),
    ]
    SUBJECT_CHOICES = [
            # Compulsory
        ('ENGLISH', 'English'),
        ('KISWAHILI', 'Kiswahili'),
        ('MATHEMATICS', 'Mathematics'),
        # Sciences
        ('BIOLOGY', 'Biology'),
        ('CHEMISTRY', 'Chemistry'),
        ('PHYSICS', 'Physics'),
        # Humanities
        ('HISTORY', 'History'),
        ('GEOGRAPHY', 'Geography'),
        ('CRE', 'Christian Religious Education'),
        ('IRE', 'Islamic Religious Education'),
        ('HRE', 'Hindu Religious Education'),
        # Languages
        ('FRENCH', 'French'),
        ('GERMAN', 'German'),
        ('ARABIC', 'Arabic'),
        # Technical
        ('HOME_SCIENCE', 'Home Science'),
        ('AGRICULTURE', 'Agriculture'),
        ('WOODWORK', 'Woodwork'),
        ('METALWORK', 'Metalwork'),
        ('BUILDING_CONSTRUCTION', 'Building Construction'),
        ('POWER_MECHANICS', 'Power Mechanics'),
        ('ELECTRICITY', 'Electricity'),
        ('DRAWING_DESIGN', 'Drawing and Design'),
        ('AVIATION', 'Aviation Technology'),
        ('COMPUTER', 'Computer Studies'),
        ('BUSINESS', 'Business Studies'),
        ('MUSIC', 'Music'),
        ('ART_DESIGN', 'Art and Design'),
    ]
        
    student = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='grades')
    subject = models.CharField(max_length=100, choices=SUBJECT_CHOICES)
    grade = models.CharField(max_length=10, choices=GRADE_CHOICES)
    points = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        editable=False  # Can't be manually edited
    )
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student', 'subject']
        ordering = ['-points']

    def __str__(self):
        return f"{self.student.user.username} - {self.subject}: {self.grade}"
    
    def save(self, *args, **kwargs):
        """Auto-calculate points from grade before saving"""
        grade_to_points = {
            'A': 12, 'A-': 11, 'B+': 10, 'B': 9, 'B-': 8,
            'C+': 7, 'C': 6, 'C-': 5, 'D+': 4, 'D': 3, 'D-': 2, 'E': 1
        }
        self.points = grade_to_points.get(self.grade, 1)
        super().save(*args, **kwargs)


class StudentPreferences(models.Model):  # Fixed typo: Prefernces -> Preferences
    student = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='preferences')
    
    # Store list of subject codes, e.g., ['MATHEMATICS', 'PHYSICS', 'CHEMISTRY']
    preferred_subjects = models.JSONField(default=list, blank=True)
    
    # Additional preference fields
    preferred_career_fields = models.JSONField(default=list, blank=True)
    preferred_institutions = models.JSONField(default=list, blank=True)
    location_preference = models.CharField(max_length=100, blank=True)
    
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Student Preferences"

    def __str__(self):
        return f"{self.student.user.username} Preferences"