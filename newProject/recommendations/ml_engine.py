import numpy as np
from collections import defaultdict


# ─────────────────────────────────────────────
# GRADE → NUMERIC MAPPING (Kenya KCSE System)
# ─────────────────────────────────────────────
GRADE_POINTS = {
    'A':  12.0,
    'A-': 11.0,
    'B+': 10.0,
    'B':  9.0,
    'B-': 8.0,
    'C+': 7.0,
    'C':  6.0,
    'C-': 5.0,
    'D+': 4.0,
    'D':  3.0,
    'D-': 2.0,
    'E':  1.0,
}

# ─────────────────────────────────────────────
# RIASEC CATEGORY → CAREER FIELD MAPPING
# ─────────────────────────────────────────────
RIASEC_CAREER_MAP = {
    'REALISTIC':     ['Engineering', 'Architecture', 'Agriculture', 'Mechanics', 'Construction'],
    'INVESTIGATIVE': ['Computer Science', 'Data Science', 'Medicine', 'Research', 'Pharmacy', 'Biology'],
    'ARTISTIC':      ['Fine Arts', 'Design', 'Music', 'Creative Writing', 'Media', 'Film'],
    'SOCIAL':        ['Education', 'Nursing', 'Social Work', 'Counseling', 'Public Health'],
    'ENTERPRISING':  ['Business', 'Law', 'Management', 'Entrepreneurship', 'Marketing'],
    'CONVENTIONAL':  ['Accounting', 'Finance', 'Administration', 'Statistics', 'Records Management'],
}

# ─────────────────────────────────────────────
# SUBJECT → RELEVANT CAREER FIELDS
# ─────────────────────────────────────────────
SUBJECT_CAREER_MAP = {
    'MATHEMATICS': ['Engineering', 'Computer Science', 'Data Science', 'Statistics',
                    'Finance', 'Accounting', 'Architecture'],
    'PHYSICS':     ['Engineering', 'Architecture', 'Computer Science', 'Software Engineering'],
    'CHEMISTRY':   ['Medicine', 'Pharmacy', 'Biology', 'Chemical Engineering', 'Agriculture', 'Nursing'],
    'BIOLOGY':     ['Medicine', 'Nursing', 'Pharmacy', 'Agriculture', 'Public Health'],
    'ENGLISH':     ['Law', 'Media', 'Education', 'Creative Writing', 'Social Work'],
    'KISWAHILI':   ['Education', 'Media', 'Social Work', 'Counseling'],
    'HISTORY':     ['Law', 'Education', 'Social Work', 'Public Administration'],
    'GEOGRAPHY':   ['Architecture', 'Agriculture', 'Environmental Science'],
    'BUSINESS':    ['Business', 'Accounting', 'Finance', 'Marketing', 'Entrepreneurship'],
    'COMPUTER':    ['Computer Science', 'Data Science', 'Software Engineering'],
}


class StudentProfileBuilder:
    """
    Builds a student profile from:
    - RIASEC psychometric scores (from assessment app)
    - Grades (from grades app)
    - Preferences (from preferences app)
    """

    def build_profile(
        self,
        riasec_scores: dict,
        grades: list[dict],
        preferences: dict
    ) -> dict:
        """
        :param riasec_scores: {
                'REALISTIC': 5, 'INVESTIGATIVE': 4, 'ARTISTIC': 3,
                'SOCIAL': 5, 'ENTERPRISING': 4, 'CONVENTIONAL': 2
              }
              — these come from the submitted assessment responses

        :param grades: [
                {'subject': 'MATHEMATICS', 'grade': 'A'},
                {'subject': 'PHYSICS', 'grade': 'B+'},
              ]
              — from the grades app

        :param preferences: {
                'preferred_subjects': ['MATHEMATICS', 'PHYSICS'],
                'preferred_career_fields': ['Engineering', 'Computer Science'],
                'preferred_institutions': ['University of Nairobi', 'JKUAT'],
                'location_preference': 'Nairobi'
              }
              — from the preferences app

        :return: Unified student profile dict used by recommenders
        """

        # ── Step 1: Get top 3 RIASEC categories by score ──
        top_riasec = sorted(riasec_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        top_riasec_categories = [r[0] for r in top_riasec]

        # ── Step 2: Map RIASEC categories → career fields ──
        riasec_career_fields = []
        for category in top_riasec_categories:
            riasec_career_fields.extend(RIASEC_CAREER_MAP.get(category, []))

        # ── Step 3: Calculate average grade points ──
        grade_values = [GRADE_POINTS.get(g['grade'], 0) for g in grades]
        avg_grade = float(np.mean(grade_values)) if grade_values else 0.0

        # ── Step 4: Identify strong subjects (B+ and above) ──
        strong_subjects = [
            g['subject'].upper() for g in grades
            if GRADE_POINTS.get(g['grade'], 0) >= 10.0  # B+ = 10.0
        ]

        # ── Step 5: Career fields implied by strong subjects ──
        subject_career_fields = []
        for subject in strong_subjects:
            subject_career_fields.extend(SUBJECT_CAREER_MAP.get(subject, []))

        # ── Step 6: Merge all career field signals ──
        pref_careers = preferences.get('preferred_career_fields', [])
        merged_careers = list(set(riasec_career_fields + subject_career_fields + pref_careers))

        # ── Step 7: Normalize RIASEC scores (0 to 1) ──
        riasec_vector = self._normalize_riasec(riasec_scores)

        return {
            'riasec_vector':          riasec_vector,
            'riasec_categories':      top_riasec_categories,
            'avg_grade':              avg_grade,
            'strong_subjects':        strong_subjects,
            'merged_career_fields':   merged_careers,
            'location_preference':    preferences.get('location_preference', ''),
            'preferred_institutions': preferences.get('preferred_institutions', []),
            'preferred_subjects':     preferences.get('preferred_subjects', []),
            'preferred_career_fields': pref_careers,
        }

    def _normalize_riasec(self, riasec_scores: dict) -> np.ndarray:
        """Scale all RIASEC scores between 0 and 1."""
        categories = ['REALISTIC', 'INVESTIGATIVE', 'ARTISTIC', 'SOCIAL', 'ENTERPRISING', 'CONVENTIONAL']
        vector = np.array([riasec_scores.get(cat, 0.0) for cat in categories], dtype=float)
        max_val = vector.max()
        if max_val > 0:
            vector = vector / max_val
        return vector


class CourseRecommender:
    """
    Scores and ranks courses based on the student's profile.

    Scoring breakdown:
    ┌──────────────────────────────────────────────┬────────┐
    │ Factor                                       │ Weight │
    ├──────────────────────────────────────────────┼────────┤
    │ Career field matches RIASEC + subject signal │  40%   │
    │ Strong subjects match required subjects      │  30%   │
    │ Student meets minimum grade requirement      │  20%   │
    │ Career field in student stated preferences   │  10%   │
    └──────────────────────────────────────────────┴────────┘
    """

    def recommend(
        self,
        student_profile: dict,
        courses: list[dict],
        top_n: int = 20  # Increased to 20 for more variety
    ) -> list[dict]:
        """
        :param student_profile: Output of StudentProfileBuilder.build_profile()
        :param courses: [
                {
                    'id': 1,
                    'name': 'Computer Science',
                    'career_field': 'Computer Science',
                    'required_subjects': ['MATHEMATICS', 'PHYSICS'],
                    'min_grade': 'B+',
                    'institution_id': 1  # Added institution_id
                }, ...
              ]
        :param top_n: Number of top courses to return
        """
        scored_courses = []

        for course in courses:
            score = self._score_course(student_profile, course)
            if score > 0:
                scored_courses.append({
                    'course_id':       course['id'],
                    'course_name':     course.get('name', ''),
                    'institution_id':  course.get('institution_id'),  # Include for diversity
                    'score':           round(score, 4),
                    'match_reasons':   self._get_match_reasons(student_profile, course)
                })

        # Sort by score
        scored_courses.sort(key=lambda x: x['score'], reverse=True)
        
        # Apply diversity algorithm to ensure multiple institutions
        return self._ensure_diversity(scored_courses, top_n)

    def _ensure_diversity(self, scored_courses: list[dict], top_n: int) -> list[dict]:
        """
        Ensure recommendations come from at least 4 different institutions.
        """
        if not scored_courses:
            return []
        
        diverse_courses = []
        institutions_seen = set()
        institutions_count = {}
        
        # First pass: count courses per institution to identify top institutions
        for course in scored_courses:
            inst_id = course.get('institution_id')
            if inst_id:
                institutions_count[inst_id] = institutions_count.get(inst_id, 0) + 1
        
        # Take top courses ensuring diversity
        for course in scored_courses:
            inst_id = course.get('institution_id')
            
            # If we have less than 4 institutions or this institution isn't represented yet
            if len(institutions_seen) < 4 or inst_id not in institutions_seen:
                diverse_courses.append(course)
                if inst_id:
                    institutions_seen.add(inst_id)
            
            # Stop if we have enough courses
            if len(diverse_courses) >= top_n:
                break
        
        # If we still need more courses, add the highest scoring remaining ones
        if len(diverse_courses) < top_n:
            for course in scored_courses:
                if course not in diverse_courses:
                    diverse_courses.append(course)
                    if len(diverse_courses) >= top_n:
                        break
        
        return diverse_courses

    def _score_course(self, profile: dict, course: dict) -> float:
        score = 0.0

        career_field      = course.get('career_field', '')
        required_subjects = [s.upper() for s in course.get('required_subjects', [])]
        min_grade         = course.get('min_grade', 'C')

        # ── 1. Career field matches merged careers (RIASEC + subjects + preferences) ──
        if career_field and career_field in profile['merged_career_fields']:
            score += 0.40
        elif not career_field:
            # If career field is empty, give a small default score
            score += 0.10

        # ── 2. Student's strong subjects match course required subjects ──
        if required_subjects:
            matching = set(profile['strong_subjects']) & set(required_subjects)
            if matching:
                subject_ratio = len(matching) / len(required_subjects)
                score += 0.30 * subject_ratio
        else:
            # If no required subjects specified, give a small default
            score += 0.15

        # ── 3. Student's average grade meets the minimum grade requirement ──
        min_grade_points = GRADE_POINTS.get(min_grade, 6.0)
        if profile['avg_grade'] >= min_grade_points:
            score += 0.20

        # ── 4. Career field is in the student's stated preferred career fields ──
        if career_field and career_field in profile.get('preferred_career_fields', []):
            score += 0.10

        return min(score, 1.0)  # Cap at 1.0

    def _get_match_reasons(self, profile: dict, course: dict) -> list[str]:
        """Human-readable explanation of why the course was recommended."""
        reasons = []

        career_field      = course.get('career_field', '')
        required_subjects = [s.upper() for s in course.get('required_subjects', [])]
        min_grade         = course.get('min_grade', 'C')

        if career_field and career_field in profile['merged_career_fields']:
            reasons.append(
                f"Aligns with your personality type: {', '.join(profile['riasec_categories'])}"
            )

        if required_subjects:
            matching = set(profile['strong_subjects']) & set(required_subjects)
            if matching:
                reasons.append(
                    f"Your strong subjects match: {', '.join(matching)}"
                )

        if profile['avg_grade'] >= GRADE_POINTS.get(min_grade, 6.0):
            reasons.append(
                f"Your grades meet the minimum requirement ({min_grade})"
            )

        if career_field and career_field in profile.get('preferred_career_fields', []):
            reasons.append(
                f"Matches your stated career interest: {career_field}"
            )

        return reasons


class UniversityRecommender:
    """
    Scores and ranks universities based on:
    - How many of the student's recommended courses they offer
    - Whether they are in the student's preferred location
    - Whether they are in the student's preferred institutions list

    Scoring breakdown:
    ┌──────────────────────────────────────────────┬────────┐
    │ Factor                                       │ Weight │
    ├──────────────────────────────────────────────┼────────┤
    │ Offers recommended courses                   │  50%   │
    │ Located in preferred location                │  30%   │
    │ In student's preferred institutions list     │  20%   │
    └──────────────────────────────────────────────┴────────┘
    """

    def recommend(
        self,
        student_profile: dict,
        recommended_course_ids: list[int],
        universities: list[dict],
        top_n: int = 10  # Increased to 10
    ) -> list[dict]:
        """
        :param student_profile: Output of StudentProfileBuilder.build_profile()
        :param recommended_course_ids: Top course IDs from CourseRecommender
        :param universities: [
                {
                    'id': 1,
                    'name': 'University of Nairobi',
                    'location': 'Nairobi',
                    'offered_course_ids': [1, 2, 3, ...]
                }, ...
              ]
        :param top_n: Number of top universities to return
        """
        scored_universities = []

        for uni in universities:
            score = self._score_university(student_profile, recommended_course_ids, uni)
            if score > 0:
                scored_universities.append({
                    'university_id':   uni['id'],
                    'university_name': uni.get('name', ''),
                    'score':           round(score, 4),
                    'match_reasons':   self._get_match_reasons(
                                           student_profile, recommended_course_ids, uni
                                       )
                })

        scored_universities.sort(key=lambda x: x['score'], reverse=True)
        return scored_universities[:top_n]

    def _score_university(
        self,
        profile: dict,
        recommended_course_ids: list[int],
        uni: dict
    ) -> float:
        score = 0.0

        offered_courses  = set(uni.get('offered_course_ids', []))
        recommended_set  = set(recommended_course_ids)

        # ── 1. Overlap between recommended courses and university's offered courses ──
        if recommended_set:
            overlap = offered_courses & recommended_set
            if overlap:
                overlap_ratio = len(overlap) / len(recommended_set)
                score += 0.50 * overlap_ratio

        # ── 2. University location matches student's location preference ──
        location_pref = profile.get('location_preference', '').strip().lower()
        uni_location  = uni.get('location', '').strip().lower()
        if location_pref and uni_location and location_pref in uni_location:
            score += 0.30

        # ── 3. University is in student's preferred institutions list ──
        if uni.get('name', '') in profile.get('preferred_institutions', []):
            score += 0.20

        return score

    def _get_match_reasons(
        self,
        profile: dict,
        recommended_course_ids: list[int],
        uni: dict
    ) -> list[str]:
        reasons = []

        offered_courses = set(uni.get('offered_course_ids', []))
        overlap         = offered_courses & set(recommended_course_ids)

        if overlap:
            reasons.append(f"Offers {len(overlap)} of your recommended courses")

        location_pref = profile.get('location_preference', '').strip().lower()
        uni_location  = uni.get('location', '').strip().lower()
        if location_pref and location_pref in uni_location:
            reasons.append(f"Located in your preferred area: {profile['location_preference']}")

        if uni.get('name', '') in profile.get('preferred_institutions', []):
            reasons.append("In your preferred institutions list")

        return reasons


class StudentRecommendationEngine:
    """
    Main entry point — orchestrates the full pipeline:

    Psychometric Test (RIASEC scores)
              +
         Grades (KCSE)
              +
        Preferences (location, career fields, institutions)
              │
              ▼
    ┌─────────────────────────┐
    │   StudentProfileBuilder │  ← merges all 3 inputs
    └────────────┬────────────┘
                 │
        ┌────────┴────────┐
        ▼                 ▼
    CourseRecommender   UniversityRecommender
        │                       │
        └────────┬──────────────┘
                 ▼
        Final Recommendations
    """

    def __init__(self):
        self.profile_builder       = StudentProfileBuilder()
        self.course_recommender    = CourseRecommender()
        self.university_recommender = UniversityRecommender()

    def recommend(
        self,
        riasec_scores: dict,
        grades: list[dict],
        preferences: dict,
        courses: list[dict],
        universities: list[dict],
        top_courses: int = 20,  # Increased default
        top_universities: int = 10,  # Increased default
    ) -> dict:
        """
        Full recommendation pipeline.

        :param riasec_scores:  {'REALISTIC': 5, 'INVESTIGATIVE': 4, ...}
        :param grades:         [{'subject': 'MATHEMATICS', 'grade': 'A'}, ...]
        :param preferences:    {'preferred_career_fields': [...], 'location_preference': 'Nairobi', ...}
        :param courses:        List of course dicts from DB
        :param universities:   List of university dicts from DB
        :param top_courses:    How many courses to recommend
        :param top_universities: How many universities to recommend

        :return: {
            'student_profile': {...},
            'recommended_courses': [...],
            'recommended_universities': [...]
        }
        """

        # ── Step 1: Build unified student profile ──
        student_profile = self.profile_builder.build_profile(
            riasec_scores=riasec_scores,
            grades=grades,
            preferences=preferences
        )

        # ── Step 2: Score and rank courses ──
        recommended_courses = self.course_recommender.recommend(
            student_profile=student_profile,
            courses=courses,
            top_n=top_courses
        )

        # ── Step 3: Score and rank universities using top course IDs ──
        top_course_ids = [c['course_id'] for c in recommended_courses]
        recommended_universities = self.university_recommender.recommend(
            student_profile=student_profile,
            recommended_course_ids=top_course_ids,
            universities=universities,
            top_n=top_universities
        )

        return {
            'student_profile': {
                'top_riasec_categories': student_profile['riasec_categories'],
                'avg_grade':             round(student_profile['avg_grade'], 2),
                'strong_subjects':       student_profile['strong_subjects'],
                'matched_career_fields': student_profile['merged_career_fields'],
            },
            'recommended_courses':      recommended_courses,
            'recommended_universities': recommended_universities,
        }