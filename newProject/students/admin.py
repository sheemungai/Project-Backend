from django.contrib import admin
from .models import Profile, StudentGrades, StudentPreferences

# Register your models here.

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'gender', 'dob', 'phone', 'createdAt']
    search_fields = ['user__username', 'user__email', 'phone']
    list_filter = ['gender', 'createdAt']


@admin.register(StudentGrades)
class StudentGradesAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'grade', 'points', 'createdAt']
    list_filter = ['grade', 'subject']
    search_fields = ['student__user__username', 'subject']
    readonly_fields = ['points']


@admin.register(StudentPreferences)
class StudentPreferencesAdmin(admin.ModelAdmin):
    list_display = ['student', 'location_preference', 'createdAt']
    search_fields = ['student__user__username']