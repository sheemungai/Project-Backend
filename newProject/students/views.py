from django.shortcuts import render
from . import serializers
from . import models
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
# from rest_framework import viewsets
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
        serializer = serializers.ProfileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)
        else:
            return Response({"status": "error", "data": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
      # updating an existing profile
    def patch(self, request, id=None):
        item = get_object_or_404(models.Profile, id=id)
        serializer = serializers.ProfileSerializer(item, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)
        else:
            return Response({"status": "error", "data": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    #  deleting a profile
    def delete(self, request, id=None):
        item = get_object_or_404(models.Profile, id=id)
        item.delete()
        return Response({"status": "success", "data": "Item Deleted"})