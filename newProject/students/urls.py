from django.urls import path
from .views import ProfileViewset


urlpatterns = [
    path('profiles/', ProfileViewset.as_view()),
    path('profiles/<int:id>/', ProfileViewset.as_view()),
]