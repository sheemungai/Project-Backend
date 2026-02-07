from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from students.models import Profile  # ← CORRECT: Import from students app

# Create your models here.
class PsychometricQuestion(models.Model):
    CATEGORY_CHOICES = [
        # RIASEC Model
        ('REALISTIC', 'Realistic'),
        ('INVESTIGATIVE', 'Investigative'),
        ('ARTISTIC', 'Artistic'),
        ('SOCIAL', 'Social'),
        ('ENTERPRISING', 'Enterprising'),
        ('CONVENTIONAL', 'Conventional'),
        # Big Five (Optional)
        ('OPENNESS', 'Openness'),
        ('CONSCIENTIOUSNESS', 'Conscientiousness'),
        ('EXTRAVERSION', 'Extraversion'),
        ('AGREEABLENESS', 'Agreeableness'),
        ('NEUROTICISM', 'Neuroticism'),
    ]
    
    question_text = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.category} - {self.question_text[:50]}"
    
    class Meta:
        ordering = ['category', 'id']


class PsychometricResponse(models.Model):
    student = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='psychometric_responses'
    )
    question = models.ForeignKey(
        PsychometricQuestion,
        on_delete=models.CASCADE
    )
    response_value = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="1=Strongly Disagree, 5=Strongly Agree"
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['student', 'question']
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.student.user.username} → Q{self.question.id}: {self.response_value}"