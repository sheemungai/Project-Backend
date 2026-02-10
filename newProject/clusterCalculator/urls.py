
from django.urls import path
from .views import  ClusterViewSet, StudentGradeViewSet, SubjectViewSet
from importlib.resources import path


urlpatterns = [
    path('subjects/', SubjectViewSet.as_view()),
    path('subjects/<int:pk>/', SubjectViewSet.as_view()),
    path('grades/', StudentGradeViewSet.as_view()),
    path('grades/<int:pk>/', StudentGradeViewSet.as_view()),
    path('clusters/', ClusterViewSet.as_view({'get': 'list'})),
    path('clusters/<int:pk>/', ClusterViewSet.as_view({'get': 'retrieve'})),
    path('student-grades/', StudentGradeViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('student-grades/<int:pk>/', StudentGradeViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),

]