from django.urls import path
from .views import MyProfileView, ProfileViewset, StudentGradesViewSet, StudentPreferencesView


urlpatterns = [
    path('profiles/', ProfileViewset.as_view()),
    path('profiles/<int:id>/', ProfileViewset.as_view()),
    path('myprofile/', MyProfileView.as_view()),


    path('grades/', StudentGradesViewSet.as_view(), name='grades-list'),
    path('grades/<int:id>/', StudentGradesViewSet.as_view(), name='grades-detail'),
    
    # Preferences endpoint
    path('preferences/', StudentPreferencesView.as_view(), name='preferences'),
]