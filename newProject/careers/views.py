from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import CareerPath, Course, Institution
from .serializers import CareerPathSerializer, CourseSerializer, InstitutionSerializer


class CareerPathViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing career paths.
    Supports list, create, retrieve, update, and delete operations.
    """
    queryset = CareerPath.objects.all()
    serializer_class = CareerPathSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class CourseViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing courses.
    Supports list, create, retrieve, update, and delete operations.
    """
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class InstitutionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing institutions.
    Supports list, create, retrieve, update, and delete operations.
    """
    queryset = Institution.objects.all()
    serializer_class = InstitutionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]