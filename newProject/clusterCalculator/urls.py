from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ClusterViewSet, 
    SubjectViewSet, 
    ClusterPointCalculationViewSet
)

router = DefaultRouter()
router.register(r'subjects', SubjectViewSet, basename='subject')
router.register(r'clusters', ClusterViewSet, basename='cluster')
router.register(r'calculations', ClusterPointCalculationViewSet, basename='calculation')

urlpatterns = [
    path('', include(router.urls)),
]