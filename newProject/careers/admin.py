from django.contrib import admin
from .models import CareerPath, Course, Institution

# Register your models here.
admin.site.register(CareerPath)
admin.site.register(Course)
admin.site.register(Institution)        