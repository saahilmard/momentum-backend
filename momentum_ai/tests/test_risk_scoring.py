import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import User, School, Student, Task, Checkin, Goal, Event, UserRole, TaskStatus, GoalStatus
from app.risk_scoring import RiskScoringEngine
from app.auth import get_password_hash

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_risk.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_school(db_session):
    school = School(name="Test School", district="Test District")
    db_session.add(school)
    db_session.commit()
    db_session.refresh(school)
    return school

@pytest.fixture
def test_student(db_session, test_school):
    user = User(
        email="student@test.com",
        password_hash=get_password_hash("password"),
        full_name="Test Student",
        role=UserRole.STUDENT,
        school_id=test_school.id
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    student = Student(
        user_id=user.id,
        grade_level="11th",
        gpa=3.2,
        risk_score=0.0
    )
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)
    return student

def test_risk_scoring_engine_initialization(db_session):
    """Test risk scoring engine initialization."""
    engine = RiskScoringEngine(db_session)
    assert engine.lookback_days == 14
    assert len(engine.weights) == 6

def test_calculate_student_risk_basic(db_session, test_student):
    """Test basic risk calculation for a student with no data."""
    engine = RiskScoringEngine(db_session)
    risk_data = engine.calculate_student_risk(test_student.id)
    
    assert "risk_score" in risk_data
    assert "factors" in risk_data
    assert "severity" in risk_data
    assert 0.0 <= risk_data["risk_score"] <= 1.0
    assert risk_data["severity"] in ["low", "medium", "high"]

def test_calculate_student_risk_with_tasks(db_session, test_student):
    """Test risk calculation with overdue tasks."""
    # Create some overdue tasks
    for i in range(3):
        task = Task(
            student_id=test_student.id,
            title=f"Task {i+1}",
            due_date=datetime.utcnow() - timedelta(days=2),
            status=TaskStatus.TODO
        )
        db_session.add(task)
    
    # Create some completed tasks
    for i in range(2):
        task = Task(
            student_id=test_student.id,
            title=f"Completed Task {i+1}",
            due_date=datetime.utcnow() - timedelta(days=1),
            status=TaskStatus.DONE,
            completed_at=datetime.utcnow() - timedelta(hours=12)
        )
        db_session.add(task)
    
    db_session.commit()
    
    engine = RiskScoringEngine(db_session)
    risk_data = engine.calculate_student_risk(test_student.id)
    
    # Should have higher risk due to overdue tasks
    assert risk_data["risk_score"] > 0.0
    assert "overdue_load" in risk_data["factors"]

def test_calculate_student_risk_with_checkins(db_session, test_student):
    """Test risk calculation with mood check-ins."""
    # Create check-ins with declining mood
    for i in range(5):
        checkin = Checkin(
            student_id=test_student.id,
            mood=5 - i,  # Declining mood: 5, 4, 3, 2, 1
            created_at=datetime.utcnow() - timedelta(days=i)
        )
        db_session.add(checkin)
    
    db_session.commit()
    
    engine = RiskScoringEngine(db_session)
    risk_data = engine.calculate_student_risk(test_student.id)
    
    assert "mood_trend" in risk_data["factors"]

def test_calculate_student_risk_with_goals(db_session, test_student):
    """Test risk calculation with goals."""
    # Create some goals
    goal1 = Goal(
        student_id=test_student.id,
        title="Goal 1",
        target_date=datetime.utcnow() + timedelta(days=7),
        status=GoalStatus.OPEN
    )
    goal2 = Goal(
        student_id=test_student.id,
        title="Goal 2",
        target_date=datetime.utcnow() - timedelta(days=1),
        status=GoalStatus.DONE
    )
    db_session.add(goal1)
    db_session.add(goal2)
    db_session.commit()
    
    engine = RiskScoringEngine(db_session)
    risk_data = engine.calculate_student_risk(test_student.id)
    
    assert "goal_velocity" in risk_data["factors"]

def test_update_student_risk_score(db_session, test_student):
    """Test updating student risk score in database."""
    engine = RiskScoringEngine(db_session)
    risk_data = engine.update_student_risk_score(test_student.id)
    
    # Check that student record was updated
    db_session.refresh(test_student)
    assert test_student.risk_score == risk_data["risk_score"]
    
    # Check that event was created
    events = db_session.query(Event).filter(
        Event.student_id == test_student.id,
        Event.type == "risk_score_updated"
    ).all()
    assert len(events) == 1

def test_get_high_risk_students(db_session, test_school):
    """Test getting high-risk students."""
    # Create multiple students with different risk scores
    students = []
    for i in range(5):
        user = User(
            email=f"student{i}@test.com",
            password_hash=get_password_hash("password"),
            full_name=f"Student {i}",
            role=UserRole.STUDENT,
            school_id=test_school.id
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        student = Student(
            user_id=user.id,
            grade_level="11th",
            risk_score=0.1 + (i * 0.2)  # 0.1, 0.3, 0.5, 0.7, 0.9
        )
        db_session.add(student)
        db_session.commit()
        db_session.refresh(student)
        students.append(student)
    
    engine = RiskScoringEngine(db_session)
    high_risk = engine.get_high_risk_students(threshold=0.6)
    
    # Should find students with risk scores >= 0.6
    assert len(high_risk) == 2  # Students with scores 0.7 and 0.9
