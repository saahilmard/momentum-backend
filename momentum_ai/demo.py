#!/usr/bin/env python3
"""
Momentum AI - Demonstration Script
Shows the core functionality of the academic recovery platform.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from app.database import SessionLocal, engine, Base
from app.models import *
from app.auth import get_password_hash, create_tokens
from app.risk_scoring import RiskScoringEngine
from datetime import datetime, timedelta
import json

def create_demo_data():
    """Create a minimal demo dataset."""
    db = SessionLocal()
    
    try:
        print("🚀 Creating Momentum AI demo data...")
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        # Create demo school
        school = School(name="Demo High School", district="Demo District")
        db.add(school)
        db.commit()
        db.refresh(school)
        print(f"✅ Created school: {school.name}")
        
        # Create admin user
        admin_user = User(
            email="admin@demo.com",
            password_hash=get_password_hash("admin123"),
            full_name="Demo Administrator",
            role=UserRole.ADMIN,
            school_id=school.id
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        print(f"✅ Created admin: {admin_user.email}")
        
        # Create mentor user
        mentor_user = User(
            email="mentor@demo.com",
            password_hash=get_password_hash("mentor123"),
            full_name="Dr. Sarah Johnson",
            role=UserRole.MENTOR,
            school_id=school.id
        )
        db.add(mentor_user)
        db.commit()
        db.refresh(mentor_user)
        
        mentor = Mentor(
            user_id=mentor_user.id,
            capacity=10,
            specialties=["Time Management", "Study Skills", "Test Anxiety"],
            meta={"experience_years": 5}
        )
        db.add(mentor)
        db.commit()
        db.refresh(mentor)
        print(f"✅ Created mentor: {mentor_user.email}")
        
        # Create student user
        student_user = User(
            email="student@demo.com",
            password_hash=get_password_hash("student123"),
            full_name="Alex Martinez",
            role=UserRole.STUDENT,
            school_id=school.id
        )
        db.add(student_user)
        db.commit()
        db.refresh(student_user)
        
        student = Student(
            user_id=student_user.id,
            grade_level="11th",
            gpa=3.2,
            risk_score=0.0,
            meta={
                "learning_style": "visual",
                "preferred_subjects": ["Math", "Science"]
            }
        )
        db.add(student)
        db.commit()
        db.refresh(student)
        print(f"✅ Created student: {student_user.email}")
        
        # Create pairing
        pairing = Pairing(
            student_id=student.id,
            mentor_id=mentor.id,
            status=PairingStatus.ACTIVE
        )
        db.add(pairing)
        db.commit()
        print("✅ Created mentor-student pairing")
        
        # Create intervention
        intervention = Intervention(
            slug="org-timeboxing",
            title="Timeboxing + 2-slot daily plan",
            category="Time Management",
            description="Break your day into focused time blocks with morning and evening planning sessions.",
            protocol={
                "cadence": "daily",
                "steps": [
                    "Plan 2 main time slots for the day (morning/evening)",
                    "Set specific tasks for each slot",
                    "Use timer for focused work periods",
                    "Review and adjust plan daily"
                ]
            }
        )
        db.add(intervention)
        db.commit()
        print("✅ Created intervention: Timeboxing")
        
        # Create some tasks
        tasks = [
            Task(
                student_id=student.id,
                title="Complete Math homework",
                due_date=datetime.utcnow() + timedelta(days=2),
                status=TaskStatus.TODO
            ),
            Task(
                student_id=student.id,
                title="Study for Science quiz",
                due_date=datetime.utcnow() + timedelta(days=1),
                status=TaskStatus.DOING
            ),
            Task(
                student_id=student.id,
                title="Read Chapter 5",
                due_date=datetime.utcnow() - timedelta(days=1),
                status=TaskStatus.DONE,
                completed_at=datetime.utcnow() - timedelta(hours=6)
            )
        ]
        
        for task in tasks:
            db.add(task)
        db.commit()
        print("✅ Created sample tasks")
        
        # Create check-ins
        checkins = [
            Checkin(
                student_id=student.id,
                mentor_id=mentor.id,
                mood=4,
                obstacles=["procrastination"],
                notes="Feeling good about progress on math homework"
            ),
            Checkin(
                student_id=student.id,
                mentor_id=mentor.id,
                mood=3,
                obstacles=["time management", "distractions"],
                notes="Struggling to focus on science study"
            )
        ]
        
        for checkin in checkins:
            db.add(checkin)
        db.commit()
        print("✅ Created sample check-ins")
        
        # Test risk scoring
        print("\n🧠 Testing risk scoring...")
        risk_engine = RiskScoringEngine(db)
        risk_data = risk_engine.calculate_student_risk(student.id)
        
        print(f"   Risk Score: {risk_data['risk_score']:.2f}")
        print(f"   Severity: {risk_data['severity']}")
        print(f"   Factors: {json.dumps(risk_data['factors'], indent=2)}")
        
        # Update student risk score
        risk_engine.update_student_risk_score(student.id)
        db.refresh(student)
        print(f"   Updated student risk score: {student.risk_score:.2f}")
        
        # Test authentication
        print("\n🔐 Testing authentication...")
        tokens = create_tokens(student_user)
        print(f"   Generated tokens for {student_user.email}")
        print(f"   Access token: {tokens['access_token'][:50]}...")
        
        print("\n🎉 Demo setup complete!")
        print("\n📊 Demo Summary:")
        print(f"   - School: {school.name}")
        print(f"   - Admin: {admin_user.email} / admin123")
        print(f"   - Mentor: {mentor_user.email} / mentor123")
        print(f"   - Student: {student_user.email} / student123")
        print(f"   - Student Risk Score: {student.risk_score:.2f}")
        print(f"   - Tasks: {len(tasks)} (1 overdue, 1 in progress, 1 completed)")
        print(f"   - Check-ins: {len(checkins)}")
        
        return {
            "school": school,
            "admin_user": admin_user,
            "mentor_user": mentor_user,
            "student_user": student_user,
            "student": student,
            "mentor": mentor,
            "intervention": intervention,
            "tokens": tokens
        }
        
    except Exception as e:
        print(f"❌ Error creating demo data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    demo_data = create_demo_data()
    print("\n🚀 Momentum AI is ready for action!")
    print("   Run 'uvicorn app.main:app --reload' to start the API server")
    print("   Visit http://localhost:8000/docs for the interactive API documentation")
