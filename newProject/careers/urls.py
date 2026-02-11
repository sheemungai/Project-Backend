from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CareerPathViewSet, CourseViewSet, InstitutionViewSet

router = DefaultRouter()
router.register(r'careerpaths', CareerPathViewSet, basename='careerpath')
router.register(r'courses', CourseViewSet, basename='course')
router.register(r'institutions', InstitutionViewSet, basename='institution')

urlpatterns = [
    path('', include(router.urls)),
]