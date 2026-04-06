# Backend/newProject/admin.py
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.db.models import Count
from django.utils.html import format_html

# Import models from your apps
from students.models import Profile, StudentGrades, StudentPreferences
from assessment.models import PsychometricQuestion, PsychometricResponse
from careers.models import CareerPath, Course, Institution
from recommendations.models import Recommendation, RecommendationSession


class CustomUserAdmin(UserAdmin):
    """Custom User Admin with statistics"""
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'has_profile', 'date_joined')
    list_filter = ('is_staff', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    
    def has_profile(self, obj):
        return hasattr(obj, 'student_profile')
    has_profile.boolean = True
    has_profile.short_description = 'Profile Complete'


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'gender', 'phone', 'grades_count', 'assessment_status', 'createdAt')
    list_filter = ('gender', 'createdAt')
    search_fields = ('user__username', 'user__email', 'phone')
    
    def grades_count(self, obj):
        return obj.grades.count()
    grades_count.short_description = 'Subjects'
    
    def assessment_status(self, obj):
        from assessment.models import PsychometricResponse
        responses = PsychometricResponse.objects.filter(student=obj)
        if responses.exists():
            return format_html('<span style="color: green;">✓ Complete</span>')
        return format_html('<span style="color: orange;">⚠ Pending</span>')
    assessment_status.short_description = 'Assessment'


class StudentGradesAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'grade', 'points', 'createdAt')
    list_filter = ('grade', 'subject', 'createdAt')
    search_fields = ('student__user__username', 'subject')
    ordering = ('-points',)


class PsychometricQuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'short_question', 'category', 'is_active', 'response_count')
    list_filter = ('category', 'is_active')
    search_fields = ('question_text',)
    list_editable = ('is_active',)
    
    def short_question(self, obj):
        return obj.question_text[:60] + '...' if len(obj.question_text) > 60 else obj.question_text
    short_question.short_description = 'Question'
    
    def response_count(self, obj):
        from assessment.models import PsychometricResponse
        return PsychometricResponse.objects.filter(question=obj).count()
    response_count.short_description = 'Responses'


class PsychometricResponseAdmin(admin.ModelAdmin):
    list_display = ('student', 'category', 'response_value', 'created_at')
    list_filter = ('question__category', 'response_value', 'created_at')
    search_fields = ('student__user__username',)
    
    def category(self, obj):
        return obj.question.category
    category.short_description = 'Category'


class CareerPathAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'avg_salary', 'growth_outlook')
    list_filter = ('category', 'growth_outlook')
    search_fields = ('name', 'description')


class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'institution', 'career_field', 'duration', 'min_grade')
    list_filter = ('institution', 'career_field', 'min_grade')
    search_fields = ('name', 'career_field')


class InstitutionAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'type', 'courses_count')
    list_filter = ('type', 'location')
    search_fields = ('name', 'location')
    
    def courses_count(self, obj):
        return obj.courses.count()
    courses_count.short_description = 'Courses'


class RecommendationAdmin(admin.ModelAdmin):
    list_display = ('user', 'item_name', 'item_type', 'score_percent', 'is_saved', 'is_seen', 'created_at')
    list_filter = ('item_type', 'is_saved', 'is_seen', 'created_at')
    search_fields = ('user__username', 'item_name')
    
    def score_percent(self, obj):
        return f"{int(obj.score * 100)}%"
    score_percent.short_description = 'Match'


class RecommendationSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'avg_grade', 'top_categories', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username',)
    
    def top_categories(self, obj):
        return ', '.join(obj.riasec_categories[:3]) if obj.riasec_categories else '-'
    top_categories.short_description = 'Top RIASEC'


# Unregister default User admin and register custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Register all models
admin.site.register(Profile, ProfileAdmin)
admin.site.register(StudentGrades, StudentGradesAdmin)
admin.site.register(PsychometricQuestion, PsychometricQuestionAdmin)
admin.site.register(PsychometricResponse, PsychometricResponseAdmin)
admin.site.register(CareerPath, CareerPathAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Institution, InstitutionAdmin)
admin.site.register(Recommendation, RecommendationAdmin)
admin.site.register(RecommendationSession, RecommendationSessionAdmin)

# Optional: Register StudentPreferences if it exists
try:
    from students.models import StudentPreferences
    admin.site.register(StudentPreferences)
except ImportError:
    pass

# Custom admin site title and header
admin.site.site_header = "Career Guidance Admin Portal"
admin.site.site_title = "Career Guidance Admin"
admin.site.index_title = "Welcome to Career Guidance Admin Dashboard"