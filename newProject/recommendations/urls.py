from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    GenerateRecommendationsView,
    RecommendationViewSet,
    RecommendationSessionViewSet,
)

router = DefaultRouter()
router.register(r'', RecommendationViewSet, basename='recommendation')
router.register(r'sessions', RecommendationSessionViewSet, basename='recommendation-session')

urlpatterns = [
    # ── Trigger ML engine ──
    path('generate/', GenerateRecommendationsView.as_view(), name='generate-recommendations'),

    # ── ViewSet routes ──
    path('', include(router.urls)),
]