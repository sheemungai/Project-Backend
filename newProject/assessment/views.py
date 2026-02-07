from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db.models import Avg, Count
from collections import defaultdict

from .models import PsychometricQuestion, PsychometricResponse
from .serializers import (
    PsychometricQuestionSerializer,
    PsychometricResponseSerializer,
    PsychometricBatchSubmissionSerializer,
    PsychometricSummarySerializer
)
from students.models import Profile


class PsychometricQuestionListView(APIView):
    """Get all active psychometric questions"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get all active questions, optionally filtered by category"""
        category = request.query_params.get('category', None)
        
        questions = PsychometricQuestion.objects.filter(is_active=True)
        
        if category:
            questions = questions.filter(category=category)
        
        questions = questions.order_by('category', 'id')
        serializer = PsychometricQuestionSerializer(questions, many=True)
        
        return Response({
            "status": "success",
            "data": serializer.data,
            "total": questions.count()
        }, status=status.HTTP_200_OK)


class PsychometricQuestionManageView(APIView):
    """Admin-only: Create, update, delete questions"""
    permission_classes = [IsAdminUser]
    
    def post(self, request):
        """Create a new question"""
        serializer = PsychometricQuestionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": "success",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": "error",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request, id):
        """Update a question"""
        question = get_object_or_404(PsychometricQuestion, id=id)
        serializer = PsychometricQuestionSerializer(question, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": "success",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        return Response({
            "status": "error",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, id):
        """Delete a question (or mark as inactive)"""
        question = get_object_or_404(PsychometricQuestion, id=id)
        # Soft delete by marking as inactive
        question.is_active = False
        question.save()
        return Response({
            "status": "success",
            "message": "Question deleted successfully"
        }, status=status.HTTP_200_OK)


class PsychometricResponseView(APIView):
    """Submit individual response"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Submit a single response"""
        try:
            profile = request.user.student_profile
        except Profile.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Student profile not found"
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = PsychometricResponseSerializer(data=request.data)
        if serializer.is_valid():
            # Check if response already exists
            question_id = serializer.validated_data['question'].id
            existing_response = PsychometricResponse.objects.filter(
                student=profile,
                question_id=question_id
            ).first()
            
            if existing_response:
                # Update existing response
                existing_response.response_value = serializer.validated_data['response_value']
                existing_response.save()
                serializer = PsychometricResponseSerializer(existing_response)
                message = "Response updated successfully"
            else:
                # Create new response
                serializer.save(student=profile)
                message = "Response submitted successfully"
            
            return Response({
                "status": "success",
                "message": message,
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            "status": "error",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class PsychometricBatchSubmissionView(APIView):
    """Submit all responses at once"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Submit multiple responses in batch"""
        try:
            profile = request.user.student_profile
        except Profile.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Student profile not found"
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = PsychometricBatchSubmissionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "status": "error",
                "data": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        responses_data = serializer.validated_data['responses']
        created_count = 0
        updated_count = 0
        
        # Process each response
        for response_data in responses_data:
            question_id = response_data['question_id']
            response_value = response_data['response_value']
            
            question = PsychometricQuestion.objects.get(id=question_id)
            
            # Update or create response
            response, created = PsychometricResponse.objects.update_or_create(
                student=profile,
                question=question,
                defaults={'response_value': response_value}
            )
            
            if created:
                created_count += 1
            else:
                updated_count += 1
        
        return Response({
            "status": "success",
            "message": "Responses submitted successfully",
            "created": created_count,
            "updated": updated_count,
            "total": len(responses_data)
        }, status=status.HTTP_201_CREATED)


class PsychometricResultsView(APIView):
    """Get student's psychometric test results"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Calculate and return test results"""
        try:
            profile = request.user.student_profile
        except Profile.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Student profile not found"
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get all responses
        responses = PsychometricResponse.objects.filter(student=profile).select_related('question')
        
        if not responses.exists():
            return Response({
                "status": "error",
                "message": "No responses found. Please complete the assessment first."
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Calculate scores by category
        category_scores = defaultdict(list)
        for response in responses:
            category_scores[response.question.category].append(response.response_value)
        
        # Calculate averages and percentages
        results_by_category = []
        for category, scores in category_scores.items():
            avg_score = sum(scores) / len(scores)
            percentage = ((avg_score - 1) / 4) * 100  # Convert 1-5 scale to 0-100%
            
            results_by_category.append({
                'category': category,
                'category_display': dict(PsychometricQuestion.CATEGORY_CHOICES).get(category),
                'score': round(avg_score, 2),
                'percentage': round(percentage, 2),
                'total_questions': len(scores)
            })
        
        # Sort by percentage (highest first)
        results_by_category.sort(key=lambda x: x['percentage'], reverse=True)
        
        # Get top 3 categories
        top_categories = results_by_category[:3]
        
        # Get total questions
        total_questions = PsychometricQuestion.objects.filter(is_active=True).count()
        total_responses = responses.count()
        completed = total_responses >= total_questions
        
        # Get latest submission time
        latest_response = responses.order_by('-submitted_at').first()
        
        return Response({
            "status": "success",
            "data": {
                "total_questions": total_questions,
                "total_responses": total_responses,
                "completed": completed,
                "completion_percentage": round((total_responses / total_questions * 100), 2) if total_questions > 0 else 0,
                "results_by_category": results_by_category,
                "top_categories": top_categories,
                "submitted_at": latest_response.submitted_at if latest_response else None
            }
        }, status=status.HTTP_200_OK)


class MyResponsesView(APIView):
    """Get student's own responses"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get all responses for authenticated user"""
        try:
            profile = request.user.student_profile
        except Profile.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Student profile not found"
            }, status=status.HTTP_404_NOT_FOUND)
        
        responses = PsychometricResponse.objects.filter(student=profile).select_related('question')
        serializer = PsychometricResponseSerializer(responses, many=True)
        
        return Response({
            "status": "success",
            "data": serializer.data,
            "total": responses.count()
        }, status=status.HTTP_200_OK)


class PsychometricProgressView(APIView):
    """Check test progress"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get progress status of psychometric test"""
        try:
            profile = request.user.student_profile
        except Profile.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Student profile not found"
            }, status=status.HTTP_404_NOT_FOUND)
        
        total_questions = PsychometricQuestion.objects.filter(is_active=True).count()
        answered_questions = PsychometricResponse.objects.filter(student=profile).count()
        
        # Get categories and their progress
        category_progress = {}
        for category_code, category_name in PsychometricQuestion.CATEGORY_CHOICES:
            total = PsychometricQuestion.objects.filter(category=category_code, is_active=True).count()
            answered = PsychometricResponse.objects.filter(
                student=profile,
                question__category=category_code
            ).count()
            
            category_progress[category_code] = {
                'category_name': category_name,
                'total': total,
                'answered': answered,
                'percentage': round((answered / total * 100), 2) if total > 0 else 0
            }
        
        completion_percentage = round((answered_questions / total_questions * 100), 2) if total_questions > 0 else 0
        
        return Response({
            "status": "success",
            "data": {
                "total_questions": total_questions,
                "answered_questions": answered_questions,
                "remaining_questions": total_questions - answered_questions,
                "completion_percentage": completion_percentage,
                "completed": answered_questions >= total_questions,
                "category_progress": category_progress
            }
        }, status=status.HTTP_200_OK)