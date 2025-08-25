#!/usr/bin/env python3
"""
Database seeding script for Momentum AI.
Creates demo schools, users, students, mentors, and interventions.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import *
from app.auth import get_password_hash
from datetime import datetime, timedelta
import random

def seed_database():
    """Seed the database with demo data."""
    db = SessionLocal()
    
    try:
        print("🌱 Seeding Momentum AI database...")
        
        # Create demo school
        print("Creating demo school...")
        school = School(
            name="Demo High School",
            district="Demo District"
        )
        db.add(school)
        db.commit()
        db.refresh(school)
        
        # Create admin user
        print("Creating admin user...")
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
        
        # Create mentor users
        print("Creating mentor users...")
        mentor_users = []
        mentor_names = [
            "Dr. Sarah Johnson", "Prof. Michael Chen", "Ms. Emily Rodriguez",
            "Dr. David Thompson", "Ms. Lisa Park"
        ]
        
        for i, name in enumerate(mentor_names):
            mentor_user = User(
                email=f"mentor{i+1}@demo.com",
                password_hash=get_password_hash("mentor123"),
                full_name=name,
                role=UserRole.MENTOR,
                school_id=school.id
            )
            db.add(mentor_user)
            db.commit()
            db.refresh(mentor_user)
            mentor_users.append(mentor_user)
        
        # Create mentor profiles
        print("Creating mentor profiles...")
        mentor_profiles = []
        specialties_list = [
            ["Time Management", "Study Skills", "Test Anxiety"],
            ["Academic Planning", "College Prep", "STEM"],
            ["Mental Health", "Stress Management", "Motivation"],
            ["Learning Disabilities", "ADHD Support", "Study Strategies"],
            ["Career Guidance", "Goal Setting", "Leadership"]
        ]
        
        for i, mentor_user in enumerate(mentor_users):
            mentor = Mentor(
                user_id=mentor_user.id,
                capacity=random.randint(8, 15),
                specialties=specialties_list[i],
                meta={"experience_years": random.randint(3, 10)}
            )
            db.add(mentor)
            db.commit()
            db.refresh(mentor)
            mentor_profiles.append(mentor)
        
        # Create student users
        print("Creating student users...")
        student_users = []
        student_names = [
            "Alex Martinez", "Jordan Kim", "Taylor Smith", "Casey Johnson",
            "Riley Brown", "Morgan Davis", "Quinn Wilson", "Avery Miller",
            "Parker Garcia", "Blake Rodriguez", "Dakota Lee", "Emery White",
            "Finley Clark", "Hayden Lewis", "Indigo Hall", "Juniper Allen",
            "Kai Young", "Luna King", "Maya Wright", "Nova Green"
        ]
        
        for i, name in enumerate(student_names):
            student_user = User(
                email=f"student{i+1}@demo.com",
                password_hash=get_password_hash("student123"),
                full_name=name,
                role=UserRole.STUDENT,
                school_id=school.id
            )
            db.add(student_user)
            db.commit()
            db.refresh(student_user)
            student_users.append(student_user)
        
        # Create student profiles
        print("Creating student profiles...")
        students = []
        grade_levels = ["9th", "10th", "11th", "12th"]
        
        for i, student_user in enumerate(student_users):
            student = Student(
                user_id=student_user.id,
                grade_level=random.choice(grade_levels),
                gpa=round(random.uniform(2.0, 4.0), 2),
                risk_score=round(random.uniform(0.0, 0.8), 2),
                meta={
                    "learning_style": random.choice(["visual", "auditory", "kinesthetic"]),
                    "preferred_subjects": random.sample(["Math", "Science", "English", "History", "Art"], 2)
                }
            )
            db.add(student)
            db.commit()
            db.refresh(student)
            students.append(student)
        
        # Create interventions
        print("Creating interventions...")
        interventions_data = [
            {
                "slug": "org-timeboxing",
                "title": "Timeboxing + 2-slot daily plan",
                "category": "Time Management",
                "description": "Break your day into focused time blocks with morning and evening planning sessions.",
                "protocol": {
                    "cadence": "daily",
                    "steps": [
                        "Plan 2 main time slots for the day (morning/evening)",
                        "Set specific tasks for each slot",
                        "Use timer for focused work periods",
                        "Review and adjust plan daily"
                    ]
                }
            },
            {
                "slug": "study-spaced-repetition",
                "title": "20-min spaced repetition blocks",
                "category": "Study Skills",
                "description": "Use spaced repetition technique with 20-minute focused study blocks.",
                "protocol": {
                    "cadence": "3x/week",
                    "steps": [
                        "Review material for 20 minutes",
                        "Take 5-minute break",
                        "Test recall of key concepts",
                        "Schedule next review based on retention"
                    ]
                }
            },
            {
                "slug": "cbt-thought-reframe",
                "title": "3-column thought reframing",
                "category": "Mental Health",
                "description": "Identify negative thoughts and reframe them using evidence-based techniques.",
                "protocol": {
                    "cadence": "as-needed",
                    "steps": [
                        "Write down negative thought",
                        "List evidence for and against",
                        "Create balanced reframe",
                        "Practice new perspective"
                    ]
                }
            },
            {
                "slug": "sleep-regularity",
                "title": "Fixed wake time + wind-down",
                "category": "Wellness",
                "description": "Establish consistent sleep schedule with evening wind-down routine.",
                "protocol": {
                    "cadence": "daily",
                    "steps": [
                        "Set consistent wake time",
                        "Create 30-minute wind-down routine",
                        "Avoid screens 1 hour before bed",
                        "Track sleep quality"
                    ]
                }
            },
            {
                "slug": "activation-5min-start",
                "title": "5-minute 'just-start' activation",
                "category": "Motivation",
                "description": "Overcome procrastination with 5-minute commitment to start tasks.",
                "protocol": {
                    "cadence": "as-needed",
                    "steps": [
                        "Commit to just 5 minutes of work",
                        "Set timer and start immediately",
                        "Continue if momentum builds",
                        "Celebrate any progress made"
                    ]
                }
            },
            {
                "slug": "pomodoro-3x",
                "title": "Three 25/5 cycles",
                "category": "Focus",
                "description": "Complete three Pomodoro cycles for challenging tasks.",
                "protocol": {
                    "cadence": "daily",
                    "steps": [
                        "Choose most important task",
                        "Work for 25 minutes",
                        "Take 5-minute break",
                        "Repeat 3 times"
                    ]
                }
            },
            {
                "slug": "deadline-backplan",
                "title": "Backward planning to sub-deadlines",
                "category": "Planning",
                "description": "Work backwards from deadlines to create sub-deadlines.",
                "protocol": {
                    "cadence": "weekly",
                    "steps": [
                        "Identify final deadline",
                        "Break into sub-tasks",
                        "Set sub-deadlines",
                        "Schedule work sessions"
                    ]
                }
            },
            {
                "slug": "accountability-ping",
                "title": "Daily mentor ping + emoji response",
                "category": "Accountability",
                "description": "Send daily progress update to mentor with emoji mood indicator.",
                "protocol": {
                    "cadence": "daily",
                    "steps": [
                        "Send brief progress update",
                        "Include emoji mood (1-5)",
                        "Mention one challenge",
                        "Ask for support if needed"
                    ]
                }
            },
            {
                "slug": "reflection-weekly",
                "title": "Friday 3-question reflection",
                "category": "Reflection",
                "description": "Weekly reflection on progress, challenges, and next steps.",
                "protocol": {
                    "cadence": "weekly",
                    "steps": [
                        "What went well this week?",
                        "What was challenging?",
                        "What's my focus for next week?",
                        "Share with mentor"
                    ]
                }
            },
            {
                "slug": "exam-warmups",
                "title": "Retrieval practice warmups",
                "category": "Study Skills",
                "description": "Use retrieval practice before study sessions to improve retention.",
                "protocol": {
                    "cadence": "before-study",
                    "steps": [
                        "Try to recall key concepts",
                        "Write down what you remember",
                        "Identify knowledge gaps",
                        "Focus study on weak areas"
                    ]
                }
            }
        ]
        
        for intervention_data in interventions_data:
            intervention = Intervention(**intervention_data)
            db.add(intervention)
        
        db.commit()
        
        # Create some pairings
        print("Creating mentor-student pairings...")
        for i, student in enumerate(students):
            mentor = mentor_profiles[i % len(mentor_profiles)]
            pairing = Pairing(
                student_id=student.id,
                mentor_id=mentor.id,
                status=PairingStatus.ACTIVE
            )
            db.add(pairing)
        
        db.commit()
        
        # Create some goals
        print("Creating sample goals...")
        goal_titles = [
            "Improve Math Grade", "Complete Science Project", "Read 3 Books",
            "Join Study Group", "Practice Time Management", "Reduce Test Anxiety"
        ]
        
        for student in students[:10]:  # First 10 students get goals
            for _ in range(random.randint(1, 3)):
                goal = Goal(
                    student_id=student.id,
                    title=random.choice(goal_titles),
                    description=f"Goal for {student.user.full_name}",
                    target_date=datetime.utcnow() + timedelta(days=random.randint(7, 30)),
                    status=random.choice([GoalStatus.OPEN, GoalStatus.DONE])
                )
                db.add(goal)
        
        db.commit()
        
        # Create some tasks
        print("Creating sample tasks...")
        task_titles = [
            "Complete homework assignment", "Study for quiz", "Read chapter 5",
            "Practice problems 1-10", "Review notes", "Prepare presentation",
            "Meet with study group", "Organize binder", "Create study schedule"
        ]
        
        for student in students[:15]:  # First 15 students get tasks
            for _ in range(random.randint(2, 5)):
                task = Task(
                    student_id=student.id,
                    title=random.choice(task_titles),
                    due_date=datetime.utcnow() + timedelta(days=random.randint(1, 14)),
                    status=random.choice([TaskStatus.TODO, TaskStatus.DOING, TaskStatus.DONE])
                )
                db.add(task)
        
        db.commit()
        
        # Create some check-ins
        print("Creating sample check-ins...")
        for student in students[:12]:  # First 12 students get check-ins
            for days_ago in range(7):  # Last 7 days
                checkin = Checkin(
                    student_id=student.id,
                    mentor_id=student.pairings[0].mentor_id if student.pairings else None,
                    mood=random.randint(1, 5),
                    obstacles=random.sample(["procrastination", "distractions", "time management", "stress"], random.randint(0, 2)),
                    notes=f"Check-in for {student.user.full_name}",
                    created_at=datetime.utcnow() - timedelta(days=days_ago)
                )
                db.add(checkin)
        
        db.commit()
        
        print("✅ Database seeded successfully!")
        print(f"📊 Created:")
        print(f"   - 1 school")
        print(f"   - 1 admin user")
        print(f"   - {len(mentor_users)} mentor users")
        print(f"   - {len(student_users)} student users")
        print(f"   - {len(interventions_data)} interventions")
        print(f"   - {len(students)} mentor-student pairings")
        print(f"   - Sample goals, tasks, and check-ins")
        
        print("\n🔑 Demo Login Credentials:")
        print("   Admin: admin@demo.com / admin123")
        print("   Mentor: mentor1@demo.com / mentor123")
        print("   Student: student1@demo.com / student123")
        
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
