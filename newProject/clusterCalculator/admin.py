from django.contrib import admin

from .models import Cluster, Grade, StudentGrade, Subject

# Register your models here.
admin.site.register(Grade)
admin.site.register(Subject)
admin.site.register(Cluster)
admin.site.register(StudentGrade)