from django.shortcuts import render
from . import serializers
from . import models
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404 



# Create your views here.
class ProfileViewset(APIView):
    # fetching profiles
    def get(self, request, id=None):
        if id:
            item = get_object_or_404(models.Profile, id=id)
            serializer = serializers.ProfileSerializer(item)
            return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)

        items = models.Profile.objects.all()
        serializer = serializers.ProfileSerializer(items, many=True)
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