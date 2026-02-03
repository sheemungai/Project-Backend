from django.db import models

# Create your models here.
class Profile(models.Model):
    firstName = models.CharField(max_length=255)
    lastName = models.CharField(max_length=255)
    email = models.EmailField(max_length=255)
    address = models.TextField()
    dob = models.DateField()
    gender = models.CharField(max_length=50)
    phone = models.CharField(max_length=20)
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return  self.lastName
    
