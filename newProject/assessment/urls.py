from django.urls import path
from .views import (
    PsychometricQuestionListView,
    PsychometricQuestionManageView,
    PsychometricResponseView,
    PsychometricBatchSubmissionView,
    PsychometricResultsView,
    MyResponsesView,
    PsychometricProgressView
)

urlpatterns = [
    # Get all active questions
    path('questions/', PsychometricQuestionListView.as_view(), name='psychometric-questions'),
    
    # Admin: Manage questions (create, update, delete)
    path('questions/manage/', PsychometricQuestionManageView.as_view(), name='psychometric-manage'),
    path('questions/manage/<int:id>/', PsychometricQuestionManageView.as_view(), name='psychometric-manage-detail'),
    
    # Submit responses
    path('response/', PsychometricResponseView.as_view(), name='psychometric-response'),
    path('submit/', PsychometricBatchSubmissionView.as_view(), name='psychometric-batch-submit'),
    
    # Get results and progress
    path('results/', PsychometricResultsView.as_view(), name='psychometric-results'),
    path('progress/', PsychometricProgressView.as_view(), name='psychometric-progress'),
    path('myresponses/', MyResponsesView.as_view(), name='my-responses'),
]