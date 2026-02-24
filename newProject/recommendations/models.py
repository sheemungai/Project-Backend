from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Recommendation(models.Model):
    """
    Stores a single ML-generated recommendation (course or institution)
    for a student.
    """

    ITEM_TYPE_CHOICES = [
        ('course', 'Course'),
        ('institution', 'Institution'),
    ]

    RECOMMENDATION_TYPE_CHOICES = [
        ('content_based', 'Content Based'),
        ('collaborative', 'Collaborative Filtering'),
        ('hybrid', 'Hybrid'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recommendations'
    )

    # ── Item being recommended ──
    item_id = models.PositiveIntegerField(
        help_text="ID of the recommended course or institution"
    )
    item_type = models.CharField(
        max_length=20,
        choices=ITEM_TYPE_CHOICES,
        help_text="Whether this is a course or institution recommendation"
    )
    item_name = models.CharField(
        max_length=255,
        help_text="Name of the recommended course or institution"
    )

    # ── ML Score ──
    score = models.FloatField(
        default=0.0,
        help_text="Relevance score from ML engine (0.0 to 1.0)"
    )
    recommendation_type = models.CharField(
        max_length=20,
        choices=RECOMMENDATION_TYPE_CHOICES,
        default='hybrid'
    )

    # ── Match reasons from ML engine ──
    match_reasons = models.JSONField(
        default=list,
        blank=True,
        help_text="List of reasons why this was recommended"
    )

    # ── Status tracking ──
    is_seen = models.BooleanField(default=False)
    is_saved = models.BooleanField(
        default=False,
        help_text="Student bookmarked this recommendation"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-score', '-created_at']
        # Prevent duplicate recommendations for same user + item
        unique_together = ['user', 'item_id', 'item_type']
        indexes = [
            models.Index(fields=['user', 'item_type']),
            models.Index(fields=['user', 'is_seen']),
            models.Index(fields=['user', 'is_saved']),
        ]

    def __str__(self):
        return (
            f"{self.user.username} → {self.item_type}: "
            f"{self.item_name} (score: {self.score:.2f})"
        )


class RecommendationSession(models.Model):
    """
    Tracks each time the ML engine runs for a student.
    Links to all recommendations generated in that session.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recommendation_sessions'
    )

    # ── Snapshot of student profile used in this session ──
    riasec_categories = models.JSONField(
        default=list,
        help_text="Top RIASEC categories at time of recommendation"
    )
    avg_grade = models.FloatField(
        default=0.0,
        help_text="Student's average grade at time of recommendation"
    )
    strong_subjects = models.JSONField(
        default=list,
        help_text="Subjects with B+ or above at time of recommendation"
    )
    matched_career_fields = models.JSONField(
        default=list,
        help_text="Career fields matched from RIASEC + grades + preferences"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Session for {self.user.username} on {self.created_at.strftime('%Y-%m-%d %H:%M')}"