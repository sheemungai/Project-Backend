from django.urls import path
from .views import CareerPathView, CourseView, InstitutionView

urlpatterns = [
    path('careerpaths/', CareerPathView.as_view()),
    path('careerpaths/<int:pk>/', CareerPathView.as_view()),
    path('courses/', CourseView.as_view()),                
    path('courses/<int:pk>/', CourseView.as_view()),
    path('institutions/', InstitutionView.as_view()),
    path('institutions/<int:pk>/', InstitutionView.as_view()),
]