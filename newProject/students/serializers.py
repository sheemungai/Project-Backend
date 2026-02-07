from rest_framework import serializers
from .models import Profile, StudentGrades, StudentPreferences

class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    class Meta:
        model = Profile
        fields = ['id', 'user', 'username', 'email', 'first_name', 'last_name', 
                  'address', 'dob', 'gender', 'phone', 'createdAt', 'updatedAt']
        read_only_fields = ['id', 'user', 'createdAt', 'updatedAt']


class StudentGradesSerializer(serializers.ModelSerializer):
    subject_display = serializers.CharField(source='get_subject_display', read_only=True)
    grade_display = serializers.CharField(source='get_grade_display', read_only=True)
    
    class Meta:
        model = StudentGrades
        fields = ['id', 'student', 'subject', 'subject_display', 'grade', 
                  'grade_display', 'points', 'createdAt', 'updatedAt']
        read_only_fields = ['id', 'student', 'points', 'createdAt', 'updatedAt']
    
    def validate(self, data):
        """Validate that student doesn't already have a grade for this subject"""
        student = self.context.get('student')
        if student and self.instance is None:  # Only on creation
            if StudentGrades.objects.filter(student=student, subject=data['subject']).exists():
                raise serializers.ValidationError(
                    f"Grade for {data['subject']} already exists. Use PATCH to update."
                )
        return data
    


class StudentPreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentPreferences
        fields = ['id', 'student', 'preferred_subjects', 'preferred_career_fields',
                  'preferred_institutions', 'location_preference', 'createdAt', 'updatedAt']
        read_only_fields = ['id', 'student', 'createdAt', 'updatedAt']
    
    def validate_preferred_subjects(self, value):
        """Validate that preferred subjects are valid"""
        if value:
            valid_subjects = [choice[0] for choice in StudentGrades.SUBJECT_CHOICES]
            for subject in value:
                if subject not in valid_subjects:
                    raise serializers.ValidationError(f"'{subject}' is not a valid subject choice")
        return value