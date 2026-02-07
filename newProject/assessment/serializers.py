from rest_framework import serializers
from .models import PsychometricQuestion, PsychometricResponse
from students.models import Profile


class PsychometricQuestionSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    class Meta:
        model = PsychometricQuestion
        fields = ['id', 'question_text', 'category', 'category_display', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class PsychometricResponseSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source='question.question_text', read_only=True)
    category = serializers.CharField(source='question.category', read_only=True)
    
    class Meta:
        model = PsychometricResponse
        fields = ['id', 'student', 'question', 'question_text', 'category', 
                  'response_value', 'submitted_at']
        read_only_fields = ['id', 'student', 'submitted_at']
    
    def validate_response_value(self, value):
        """Validate response is between 1-5"""
        if value < 1 or value > 5:
            raise serializers.ValidationError("Response value must be between 1 and 5")
        return value


class PsychometricBatchSubmissionSerializer(serializers.Serializer):
    """Serializer for submitting multiple responses at once"""
    responses = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=False
    )
    
    def validate_responses(self, value):
        """Validate the batch of responses"""
        if not value:
            raise serializers.ValidationError("Responses cannot be empty")
        
        for response in value:
            # Check required fields
            if 'question_id' not in response:
                raise serializers.ValidationError("Each response must have 'question_id'")
            if 'response_value' not in response:
                raise serializers.ValidationError("Each response must have 'response_value'")
            
            # Validate response value range
            response_value = response.get('response_value')
            if not isinstance(response_value, int) or response_value < 1 or response_value > 5:
                raise serializers.ValidationError(
                    f"Response value must be an integer between 1 and 5, got {response_value}"
                )
            
            # Check if question exists
            question_id = response.get('question_id')
            if not PsychometricQuestion.objects.filter(id=question_id, is_active=True).exists():
                raise serializers.ValidationError(f"Question with id {question_id} does not exist or is inactive")
        
        return value


class PsychometricResultSerializer(serializers.Serializer):
    """Serializer for displaying psychometric test results"""
    category = serializers.CharField()
    score = serializers.FloatField()
    percentage = serializers.FloatField()
    
    
class PsychometricSummarySerializer(serializers.Serializer):
    """Serializer for overall test summary"""
    total_questions = serializers.IntegerField()
    total_responses = serializers.IntegerField()
    completed = serializers.BooleanField()
    results_by_category = PsychometricResultSerializer(many=True)
    top_categories = serializers.ListField(
        child=serializers.DictField()
    )
    submitted_at = serializers.DateTimeField()