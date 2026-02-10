from django.urls import path
from .views import CareerPathViewSet, CourseViewSet, InstitutionViewSet

urlpatterns = [
    path('careerpaths/', CareerPathViewSet.as_view()),
    path('careerpaths/<int:pk>/', CareerPathViewSet.as_view()),
    path('courses/', CourseViewSet.as_view()),                
    path('courses/<int:pk>/', CourseViewSet.as_view()),
    path('institutions/', InstitutionViewSet.as_view()),
    path('institutions/<int:pk>/', InstitutionViewSet.as_view()),
]