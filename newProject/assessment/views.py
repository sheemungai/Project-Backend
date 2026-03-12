# assessment/views.py
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
        errors = []
        
        # Process each response
        for response_data in responses_data:
            question_id = response_data['question_id']
            response_value = response_data['response_value']
            
            try:
                question = PsychometricQuestion.objects.get(id=question_id, is_active=True)
                
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
                    
            except PsychometricQuestion.DoesNotExist:
                errors.append(f"Question {question_id} not found or inactive")
            except Exception as e:
                errors.append(f"Error for question {question_id}: {str(e)}")
        
        # Check if test is now complete
        total_questions = PsychometricQuestion.objects.filter(is_active=True).count()
        answered_questions = PsychometricResponse.objects.filter(
            student=profile
        ).values('question').distinct().count()
        
        is_complete = answered_questions >= total_questions if total_questions > 0 else False
        
        response_data = {
            "status": "success" if not errors else "partial",
            "message": "Responses submitted successfully",
            "created": created_count,
            "updated": updated_count,
            "total": len(responses_data),
            "errors": errors if errors else None,
            "is_complete": is_complete,
            "progress": {
                "answered": answered_questions,
                "total": total_questions,
                "percentage": round((answered_questions / total_questions * 100), 2) if total_questions > 0 else 0,
                "remaining": total_questions - answered_questions
            }
        }
        
        # AUTO-TRIGGER RECOMMENDATIONS if test is now complete
        if is_complete:
            try:
                from recommendations.services import generate_student_recommendations
                
                # Check if grades exist
                if profile.grades.exists():
                    recommendations = generate_student_recommendations(request.user)
                    response_data["recommendations_generated"] = True
                    response_data["recommendations"] = recommendations
                    response_data["message"] += " Your personalized recommendations are ready!"
                else:
                    response_data["recommendations_generated"] = False
                    response_data["message"] += " Please enter your KCSE grades to get personalized recommendations."
            except ImportError:
                response_data["recommendations_generated"] = False
                response_data["recommendation_error"] = "Recommendations service not available"
            except Exception as e:
                response_data["recommendations_generated"] = False
                response_data["recommendation_error"] = str(e)
        
        return Response(response_data, status=status.HTTP_201_CREATED)


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
        
        # Get all responses (distinct questions only)
        responses = PsychometricResponse.objects.filter(
            student=profile
        ).select_related('question').order_by('question__category')
        
        if not responses.exists():
            return Response({
                "status": "error",
                "message": "No responses found. Please complete the assessment first."
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Calculate scores by category - using distinct questions per category
        category_scores = defaultdict(list)
        processed_questions = set()
        
        for response in responses:
            question_id = response.question.id
            if question_id not in processed_questions:
                category_scores[response.question.category].append(response.response_value)
                processed_questions.add(question_id)
        
        # Calculate averages and percentages
        results_by_category = []
        for category, scores in category_scores.items():
            avg_score = sum(scores) / len(scores)
            percentage = ((avg_score - 1) / 4) * 100  # Convert 1-5 scale to 0-100%
            
            # Determine interpretation
            if percentage >= 75:
                interpretation = "Very High"
            elif percentage >= 60:
                interpretation = "High"
            elif percentage >= 40:
                interpretation = "Moderate"
            elif percentage >= 25:
                interpretation = "Low"
            else:
                interpretation = "Very Low"
            
            results_by_category.append({
                'category': category,
                'category_display': dict(PsychometricQuestion.CATEGORY_CHOICES).get(category, category),
                'score': round(avg_score, 2),
                'percentage': round(percentage, 2),
                'interpretation': interpretation,
                'total_questions': len(scores)
            })
        
        # Sort by percentage (highest first)
        results_by_category.sort(key=lambda x: x['percentage'], reverse=True)
        
        # Get top 3 categories
        top_categories = results_by_category[:3]
        
        # Get total questions
        total_questions = PsychometricQuestion.objects.filter(is_active=True).count()
        total_responses = len(processed_questions)  # Use distinct questions count
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
        
        responses = PsychometricResponse.objects.filter(
            student=profile
        ).select_related('question').order_by('question__category', 'question__id')
        
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
        
        # Get total active questions
        total_questions = PsychometricQuestion.objects.filter(is_active=True).count()
        
        # IMPORTANT: Use distinct('question') to count unique questions answered
        # This prevents double-counting if student answered same question multiple times
        answered_questions = PsychometricResponse.objects.filter(
            student=profile
        ).values('question').distinct().count()
        
        # Check if test is complete
        is_complete = answered_questions >= total_questions if total_questions > 0 else False
        
        # Calculate completion percentage
        completion_percentage = round((answered_questions / total_questions * 100), 2) if total_questions > 0 else 0
        
        # Get categories and their progress
        category_progress = {}
        for category_code, category_name in PsychometricQuestion.CATEGORY_CHOICES:
            total_in_category = PsychometricQuestion.objects.filter(
                category=category_code, 
                is_active=True
            ).count()
            
            answered_in_category = PsychometricResponse.objects.filter(
                student=profile,
                question__category=category_code
            ).values('question').distinct().count()
            
            category_progress[category_code] = {
                'category_name': category_name,
                'total': total_in_category,
                'answered': answered_in_category,
                'percentage': round((answered_in_category / total_in_category * 100), 2) if total_in_category > 0 else 0,
                'is_complete': answered_in_category >= total_in_category if total_in_category > 0 else False
            }
        
        # Return in the format expected by frontend
        return Response({
            "status": "success",
            "data": {
                "total_questions": total_questions,
                "answered": answered_questions,
                "remaining": total_questions - answered_questions,
                "percentage": completion_percentage,
                "is_complete": is_complete,
                "category_progress": category_progress
            }
        }, status=status.HTTP_200_OK)


class DebugPsychometricView(APIView):
    """Debug endpoint to check what's in the database (TEMPORARY)"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Debug endpoint to check database state"""
        try:
            profile = request.user.student_profile
            
            # Get all questions
            questions = PsychometricQuestion.objects.filter(is_active=True)
            total_questions = questions.count()
            
            # Get all responses for this user
            responses = PsychometricResponse.objects.filter(student=profile)
            total_responses = responses.count()
            
            # Get unique questions answered
            unique_questions = responses.values('question').distinct().count()
            
            # Check for duplicate responses
            from django.db.models import Count
            duplicates_qs = responses.values('question').annotate(
                count=Count('id')
            ).filter(count__gt=1)
            
            duplicates = {}
            for item in duplicates_qs:
                question_id = item['question']
                question_text = PsychometricQuestion.objects.get(id=question_id).question_text[:50]
                duplicates[question_id] = {
                    'count': item['count'],
                    'question_text': question_text
                }
            
            # Category breakdown
            category_breakdown = {}
            for category_code, category_name in PsychometricQuestion.CATEGORY_CHOICES:
                total_in_cat = questions.filter(category=category_code).count()
                unique_in_cat = responses.filter(
                    question__category=category_code
                ).values('question').distinct().count()
                
                category_breakdown[category_code] = {
                    'name': category_name,
                    'total': total_in_cat,
                    'unique_answered': unique_in_cat,
                    'percentage': round((unique_in_cat / total_in_cat * 100), 2) if total_in_cat > 0 else 0
                }
            
            return Response({
                "user": request.user.username,
                "profile_exists": True,
                "total_questions": total_questions,
                "total_responses": total_responses,
                "unique_questions_answered": unique_questions,
                "has_duplicates": len(duplicates) > 0,
                "duplicates": duplicates,
                "is_complete": unique_questions >= total_questions,
                "percentage": round((unique_questions / total_questions * 100), 2) if total_questions > 0 else 0,
                "category_breakdown": category_breakdown
            })
        except Profile.DoesNotExist:
            return Response({
                "user": request.user.username,
                "profile_exists": False,
                "error": "Student profile not found"
            })
        except Exception as e:
            return Response({
                "error": str(e),
                "user": request.user.username
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Optional: Add a view to reset assessment (for testing)
class ResetAssessmentView(APIView):
    """Reset student's assessment responses (for testing)"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Delete all responses for the current user"""
        try:
            profile = request.user.student_profile
            
            # Count before deletion
            count = PsychometricResponse.objects.filter(student=profile).count()
            
            # Delete all responses
            PsychometricResponse.objects.filter(student=profile).delete()
            
            return Response({
                "status": "success",
                "message": f"Successfully deleted {count} responses",
                "deleted_count": count
            }, status=status.HTTP_200_OK)
            
        except Profile.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Student profile not found"
            }, status=status.HTTP_404_NOT_FOUND)