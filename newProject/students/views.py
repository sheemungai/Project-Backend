from django.shortcuts import render
from . import serializers
from . import models
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404 
from django.db.models import Avg, Sum



# Create your views here.
class ProfileViewset(APIView):
    # fetching profiles
    def get(self, request, id=None):
        """
        - Students can ONLY view their own profile
        - Admins can view any profile or all profiles
        """
        if id:
            # Get specific profile
            profile = get_object_or_404(models.Profile, id=id)
            
            # Security check: Only owner or admin can view
            if profile.user != request.user and not request.user.is_staff:
                return Response(
                    {"status": "error", "message": "You can only view your own profile"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = serializers.ProfileSerializer(profile)
            return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)
        
        # List all profiles - ONLY ADMINS
        if not request.user.is_staff:
            return Response(
                {"status": "error", "message": "Only admins can view all profiles"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        profiles = models.Profile.objects.all()
        serializer = serializers.ProfileSerializer(profiles, many=True)
        return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)

   
      # creating a profile
    def post(self, request):

        if hasattr(request.user, 'student_profile'):
            return Response(
                {"status": "error", "message": "Profile already exists for this user."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = serializers.ProfileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)
        else:
            return Response({"status": "error", "data": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
      # updating an existing profile
    def patch(self, request, id=None):
        item = get_object_or_404(models.Profile, id=id)

          # Check if user owns this profile
        if item.user != request.user and not request.user.is_staff:
            return Response(
                {"status": "error", "message": "You can only update your own profile"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = serializers.ProfileSerializer(item, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)
        else:
            return Response({"status": "error", "data": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    #  deleting a profile
    def delete(self, request, id=None):
        item = get_object_or_404(models.Profile, id=id)
        # check if profile exist
        if item.user != request.user and not request.user.is_staff:
            return Response(
                {"status": "error", "message": "You can only delete your own profile"}, 
                status=status.HTTP_403_FORBIDDEN
            )

        item.delete()
        return Response({"status": "success", "data": "Item Deleted"})
    
class MyProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get the authenticated user's profile"""
        try:
            profile = request.user.student_profile
            serializer = serializers.ProfileSerializer(profile)
            return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)
        except models.Profile.DoesNotExist:
            return Response(
                {"status": "error", "message": "Profile not found. Please create one."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
class StudentGradesViewSet(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, id=None):
        """Get student's grades"""
        try:
            profile = request.user.student_profile
        except models.Profile.DoesNotExist:
            return Response(
                {"status": "error", "message": "Student profile not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if id:
            grade = get_object_or_404(models.StudentGrades, id=id, student=profile)
            serializer = serializers.StudentGradesSerializer(grade)
            return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)
        
        # Get all grades for the student
        grades = models.StudentGrades.objects.filter(student=profile)
        serializer = serializers.StudentGradesSerializer(grades, many=True)
        
        # Calculate statistics
        total_points = grades.aggregate(Sum('points'))['points__sum'] or 0
        avg_points = grades.aggregate(Avg('points'))['points__avg'] or 0
        total_subjects = grades.count()
        
        # Calculate mean grade
        mean_grade = self._calculate_mean_grade(avg_points)
        
        return Response({
            "status": "success",
            "data": serializer.data,
            "statistics": {
                "total_subjects": total_subjects,
                "total_points": total_points,
                "average_points": round(avg_points, 2),
                "mean_grade": mean_grade
            }
        }, status=status.HTTP_200_OK)
    
    def post(self, request):
        """Add a subject grade"""
        try:
            profile = request.user.student_profile
        except models.Profile.DoesNotExist:
            return Response(
                {"status": "error", "message": "Student profile not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = serializers.StudentGradesSerializer(
            data=request.data,
            context={'student': profile}
        )
        if serializer.is_valid():
            serializer.save(student=profile)
            return Response({"status": "success", "data": serializer.data}, status=status.HTTP_201_CREATED)
        return Response({"status": "error", "data": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request, id=None):
        """Update a subject grade"""
        try:
            profile = request.user.student_profile
        except models.Profile.DoesNotExist:
            return Response(
                {"status": "error", "message": "Student profile not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        grade = get_object_or_404(models.StudentGrades, id=id, student=profile)
        serializer = serializers.StudentGradesSerializer(grade, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)
        return Response({"status": "error", "data": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, id=None):
        """Delete a subject grade"""
        try:
            profile = request.user.student_profile
        except models.Profile.DoesNotExist:
            return Response(
                {"status": "error", "message": "Student profile not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        grade = get_object_or_404(models.StudentGrades, id=id, student=profile)
        grade.delete()
        return Response({"status": "success", "message": "Grade deleted successfully"}, status=status.HTTP_200_OK)
    
    def _calculate_mean_grade(self, avg_points):
        """Calculate KCSE mean grade from average points"""
        if avg_points >= 11: return 'A'
        elif avg_points >= 10: return 'A-'
        elif avg_points >= 9: return 'B+'
        elif avg_points >= 8: return 'B'
        elif avg_points >= 7: return 'B-'
        elif avg_points >= 6: return 'C+'
        elif avg_points >= 5: return 'C'
        elif avg_points >= 4: return 'C-'
        elif avg_points >= 3: return 'D+'
        elif avg_points >= 2: return 'D'
        elif avg_points >= 1: return 'D-'
        else: return 'E'


# Student Preferences Views
class StudentPreferencesView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get student preferences"""
        try:
            profile = request.user.student_profile
            preferences, created = models.StudentPreferences.objects.get_or_create(student=profile)
            serializer = serializers.StudentPreferencesSerializer(preferences)
            return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)
        except models.Profile.DoesNotExist:
            return Response(
                {"status": "error", "message": "Student profile not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    def post(self, request):
        """Create/Update student preferences"""
        try:
            profile = request.user.student_profile
        except models.Profile.DoesNotExist:
            return Response(
                {"status": "error", "message": "Student profile not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        preferences, created = models.StudentPreferences.objects.get_or_create(student=profile)
        serializer = serializers.StudentPreferencesSerializer(preferences, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)
        return Response({"status": "error", "data": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request):
        """Update student preferences"""
        return self.post(request)  # Same logic as POST