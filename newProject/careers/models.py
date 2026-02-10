from unicodedata import name
from django.db import models

# Create your models here.
class CareerPath(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    required_skills = models.TextField()
    average_salary = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    

class Course(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    career_paths = models.ManyToManyField(CareerPath, related_name='courses')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
class Institution(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100) 
    courses = models.ManyToManyField(Course, related_name='institutions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name