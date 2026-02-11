from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClusterViewSet, StudentGradeViewSet, SubjectViewSet

router = DefaultRouter()
router.register(r'subjects', SubjectViewSet, basename='subject')
router.register(r'grades', StudentGradeViewSet, basename='studentgrade')
router.register(r'clusters', ClusterViewSet, basename='cluster')

urlpatterns = [
    path('', include(router.urls)),
]