from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from app.models import Student, Task, Checkin, Goal, Event, TaskStatus, GoalStatus
import math


class RiskScoringEngine:
    """Engine for calculating student risk scores to detect academic spirals."""
    
    def __init__(self, db: Session):
        self.db = db
        self.lookback_days = 14
        self.weights = {
            'overdue_load': 0.30,
            'mood_trend': 0.20,
            'streak': 0.15,
            'engagement': 0.15,
            'goal_velocity': 0.10,
            'gpa_trend': 0.10
        }
    
    def calculate_student_risk(self, student_id: int) -> Dict[str, float]:
        """Calculate comprehensive risk score for a student."""
        cutoff_date = datetime.utcnow() - timedelta(days=self.lookback_days)
        
        # Get student data
        student = self.db.query(Student).filter(Student.id == student_id).first()
        if not student:
            raise ValueError(f"Student {student_id} not found")
        
        # Calculate individual risk factors
        overdue_load = self._calculate_overdue_load(student_id, cutoff_date)
        mood_trend = self._calculate_mood_trend(student_id, cutoff_date)
        streak = self._calculate_streak(student_id, cutoff_date)
        engagement = self._calculate_engagement(student_id, cutoff_date)
        goal_velocity = self._calculate_goal_velocity(student_id, cutoff_date)
        gpa_trend = self._calculate_gpa_trend(student_id, cutoff_date)
        
        # Normalize factors to [0, 1] range
        normalized_factors = {
            'overdue_load': self._normalize_overdue_load(overdue_load),
            'mood_trend': self._normalize_mood_trend(mood_trend),
            'streak': self._normalize_streak(streak),
            'engagement': self._normalize_engagement(engagement),
            'goal_velocity': self._normalize_goal_velocity(goal_velocity),
            'gpa_trend': self._normalize_gpa_trend(gpa_trend)
        }
        
        # Calculate weighted risk score
        risk_score = sum(
            self.weights[factor] * normalized_factors[factor]
            for factor in self.weights.keys()
        )
        
        # Ensure risk score is in [0, 1] range
        risk_score = max(0.0, min(1.0, risk_score))
        
        return {
            'risk_score': risk_score,
            'factors': {
                'overdue_load': overdue_load,
                'mood_trend': mood_trend,
                'streak': streak,
                'engagement': engagement,
                'goal_velocity': goal_velocity,
                'gpa_trend': gpa_trend
            },
            'normalized_factors': normalized_factors,
            'severity': self._get_severity(risk_score)
        }
    
    def _calculate_overdue_load(self, student_id: int, cutoff_date: datetime) -> float:
        """Calculate fraction of open tasks that are overdue."""
        total_open = self.db.query(Task).filter(
            and_(
                Task.student_id == student_id,
                Task.status.in_([TaskStatus.TODO, TaskStatus.DOING]),
                Task.due_date >= cutoff_date
            )
        ).count()
        
        overdue = self.db.query(Task).filter(
            and_(
                Task.student_id == student_id,
                Task.status.in_([TaskStatus.TODO, TaskStatus.DOING]),
                Task.due_date < datetime.utcnow(),
                Task.due_date >= cutoff_date
            )
        ).count()
        
        return overdue / max(total_open, 1)
    
    def _calculate_mood_trend(self, student_id: int, cutoff_date: datetime) -> float:
        """Calculate mood trend (delta of avg mood vs prior period)."""
        # Current period mood average
        current_moods = self.db.query(Checkin.mood).filter(
            and_(
                Checkin.student_id == student_id,
                Checkin.created_at >= cutoff_date,
                Checkin.mood.isnot(None)
            )
        ).all()
        
        if not current_moods:
            return 0.0
        
        current_avg = sum(mood[0] for mood in current_moods) / len(current_moods)
        
        # Prior period mood average
        prior_start = cutoff_date - timedelta(days=self.lookback_days)
        prior_moods = self.db.query(Checkin.mood).filter(
            and_(
                Checkin.student_id == student_id,
                Checkin.created_at >= prior_start,
                Checkin.created_at < cutoff_date,
                Checkin.mood.isnot(None)
            )
        ).all()
        
        if not prior_moods:
            return 0.0
        
        prior_avg = sum(mood[0] for mood in prior_moods) / len(prior_moods)
        
        # Return negative trend (lower mood = higher risk)
        return prior_avg - current_avg
    
    def _calculate_streak(self, student_id: int, cutoff_date: datetime) -> int:
        """Calculate current streak of days with completed tasks."""
        completed_tasks = self.db.query(Task.completed_at).filter(
            and_(
                Task.student_id == student_id,
                Task.status == TaskStatus.DONE,
                Task.completed_at >= cutoff_date
            )
        ).all()
        
        if not completed_tasks:
            return 0
        
        # Get unique dates with completed tasks
        completion_dates = set(
            task[0].date() for task in completed_tasks if task[0]
        )
        
        # Calculate current streak
        current_date = datetime.utcnow().date()
        streak = 0
        
        for i in range(self.lookback_days):
            check_date = current_date - timedelta(days=i)
            if check_date in completion_dates:
                streak += 1
            else:
                break
        
        return streak
    
    def _calculate_engagement(self, student_id: int, cutoff_date: datetime) -> int:
        """Calculate engagement gap (days since last check-in)."""
        last_checkin = self.db.query(Checkin.created_at).filter(
            and_(
                Checkin.student_id == student_id,
                Checkin.created_at >= cutoff_date
            )
        ).order_by(Checkin.created_at.desc()).first()
        
        if not last_checkin:
            return self.lookback_days
        
        days_since = (datetime.utcnow() - last_checkin[0]).days
        return days_since
    
    def _calculate_goal_velocity(self, student_id: int, cutoff_date: datetime) -> float:
        """Calculate percentage of goals completed on/before target date."""
        recent_goals = self.db.query(Goal).filter(
            and_(
                Goal.student_id == student_id,
                Goal.target_date >= cutoff_date
            )
        ).all()
        
        if not recent_goals:
            return 1.0  # No goals = no risk
        
        completed_on_time = 0
        total_goals = len(recent_goals)
        
        for goal in recent_goals:
            if goal.status == GoalStatus.DONE:
                if goal.target_date and goal.target_date >= datetime.utcnow():
                    completed_on_time += 1
                elif not goal.target_date:
                    completed_on_time += 1
        
        return completed_on_time / total_goals
    
    def _calculate_gpa_trend(self, student_id: int, cutoff_date: datetime) -> float:
        """Calculate GPA trend (placeholder - would need historical GPA data)."""
        # This is a placeholder implementation
        # In a real system, you'd track GPA changes over time
        student = self.db.query(Student).filter(Student.id == student_id).first()
        if not student or not student.gpa:
            return 0.0
        
        # For now, return a neutral value
        # In production, you'd compare current GPA to historical average
        return 0.0
    
    def _normalize_overdue_load(self, overdue_load: float) -> float:
        """Normalize overdue load to [0, 1] range."""
        return min(1.0, overdue_load)
    
    def _normalize_mood_trend(self, mood_trend: float) -> float:
        """Normalize mood trend to [0, 1] range."""
        # Convert to positive scale where higher = worse
        return max(0.0, min(1.0, (mood_trend + 2) / 4))
    
    def _normalize_streak(self, streak: int) -> float:
        """Normalize streak to [0, 1] range (inverted - longer streak = lower risk)."""
        # Normalize to [0, 1] and invert (longer streak = lower risk)
        normalized = min(1.0, streak / 7)  # 7 days = perfect
        return 1.0 - normalized
    
    def _normalize_engagement(self, engagement_gap: int) -> float:
        """Normalize engagement gap to [0, 1] range."""
        return min(1.0, engagement_gap / 7)  # 7 days = max risk
    
    def _normalize_goal_velocity(self, goal_velocity: float) -> float:
        """Normalize goal velocity to [0, 1] range (inverted)."""
        return 1.0 - goal_velocity
    
    def _normalize_gpa_trend(self, gpa_trend: float) -> float:
        """Normalize GPA trend to [0, 1] range."""
        # Placeholder - would need historical data
        return 0.5
    
    def _get_severity(self, risk_score: float) -> str:
        """Get severity level based on risk score."""
        if risk_score < 0.33:
            return "low"
        elif risk_score < 0.66:
            return "medium"
        else:
            return "high"
    
    def update_student_risk_score(self, student_id: int) -> Dict[str, float]:
        """Update a student's risk score in the database."""
        risk_data = self.calculate_student_risk(student_id)
        
        # Update student record
        student = self.db.query(Student).filter(Student.id == student_id).first()
        if student:
            student.risk_score = risk_data['risk_score']
            
            # Create audit event
            event = Event(
                student_id=student_id,
                type="risk_score_updated",
                payload={
                    "risk_score": risk_data['risk_score'],
                    "severity": risk_data['severity'],
                    "factors": risk_data['factors']
                }
            )
            self.db.add(event)
            self.db.commit()
        
        return risk_data
    
    def get_high_risk_students(self, threshold: float = 0.66) -> List[Dict]:
        """Get all students with risk scores above threshold."""
        high_risk_students = self.db.query(Student).filter(
            Student.risk_score >= threshold
        ).all()
        
        return [
            {
                "student_id": student.id,
                "risk_score": student.risk_score,
                "user": {
                    "id": student.user.id,
                    "full_name": student.user.full_name,
                    "email": student.user.email
                }
            }
            for student in high_risk_students
        ]
