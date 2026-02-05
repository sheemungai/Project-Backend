from django.urls import path
from .views import MyProfileView, ProfileViewset


urlpatterns = [
    path('profiles/', ProfileViewset.as_view()),
    path('profiles/<int:id>/', ProfileViewset.as_view()),
    path('myprofile/', MyProfileView.as_view()),
]