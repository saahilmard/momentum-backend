from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, ForeignKey, 
    Text, Numeric, Float, Enum, JSON, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class UserRole(str, enum.Enum):
    STUDENT = "student"
    MENTOR = "mentor"
    ADMIN = "admin"


class PairingStatus(str, enum.Enum):
    ACTIVE = "active"
    ENDED = "ended"
    PAUSED = "paused"


class TaskStatus(str, enum.Enum):
    TODO = "todo"
    DOING = "doing"
    DONE = "done"
    OVERDUE = "overdue"


class GoalStatus(str, enum.Enum):
    OPEN = "open"
    DONE = "done"
    PAUSED = "paused"


class School(Base):
    __tablename__ = "schools"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    district = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    users = relationship("User", back_populates="school")


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    school = relationship("School", back_populates="users")
    student = relationship("Student", back_populates="user", uselist=False)
    mentor = relationship("Mentor", back_populates="user", uselist=False)
    sent_messages = relationship("Message", foreign_keys="Message.sender_user_id", back_populates="sender")
    received_messages = relationship("Message", foreign_keys="Message.recipient_user_id", back_populates="recipient")
    created_plans = relationship("Plan", foreign_keys="Plan.created_by", back_populates="creator")
    attachments = relationship("Attachment", back_populates="owner")


class Student(Base):
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    grade_level = Column(String(50))
    gpa = Column(Numeric(3, 2))
    risk_score = Column(Float, default=0.0)
    meta = Column(JSON)
    
    # Relationships
    user = relationship("User", back_populates="student")
    pairings = relationship("Pairing", back_populates="student")
    plans = relationship("Plan", back_populates="student")
    goals = relationship("Goal", back_populates="student")
    tasks = relationship("Task", back_populates="student")
    checkins = relationship("Checkin", back_populates="student")
    transcripts = relationship("Transcript", back_populates="student")
    events = relationship("Event", back_populates="student")


class Mentor(Base):
    __tablename__ = "mentors"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    capacity = Column(Integer, default=10)
    specialties = Column(JSON)  # Store as JSON array for SQLite compatibility
    meta = Column(JSON)
    
    # Relationships
    user = relationship("User", back_populates="mentor")
    pairings = relationship("Pairing", back_populates="mentor")
    checkins = relationship("Checkin", back_populates="mentor")
    transcripts = relationship("Transcript", back_populates="mentor")


class Pairing(Base):
    __tablename__ = "pairings"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    mentor_id = Column(Integer, ForeignKey("mentors.id"), nullable=False)
    status = Column(Enum(PairingStatus), default=PairingStatus.ACTIVE)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True))
    
    # Relationships
    student = relationship("Student", back_populates="pairings")
    mentor = relationship("Mentor", back_populates="pairings")


class Intervention(Base):
    __tablename__ = "interventions"
    
    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    category = Column(String(100))
    description = Column(Text)
    protocol = Column(JSON)


class Plan(Base):
    __tablename__ = "plans"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    version = Column(Integer, default=1)
    active = Column(Boolean, default=False)
    plan = Column(JSON, nullable=False)  # Contains intervention items
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    student = relationship("Student", back_populates="plans")
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_plans")


class Goal(Base):
    __tablename__ = "goals"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    target_date = Column(DateTime(timezone=True))
    status = Column(Enum(GoalStatus), default=GoalStatus.OPEN)
    
    # Relationships
    student = relationship("Student", back_populates="goals")
    tasks = relationship("Task", back_populates="goal")


class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    title = Column(String(255), nullable=False)
    due_date = Column(DateTime(timezone=True))
    status = Column(Enum(TaskStatus), default=TaskStatus.TODO)
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    goal = relationship("Goal", back_populates="tasks")
    student = relationship("Student", back_populates="tasks")


class Checkin(Base):
    __tablename__ = "checkins"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    mentor_id = Column(Integer, ForeignKey("mentors.id"), nullable=True)
    mood = Column(Integer)  # 1-5 scale
    obstacles = Column(JSON)  # Store as JSON array for SQLite compatibility
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    student = relationship("Student", back_populates="checkins")
    mentor = relationship("Mentor", back_populates="checkins")


class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    sender_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipient_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    sender = relationship("User", foreign_keys=[sender_user_id], back_populates="sent_messages")
    recipient = relationship("User", foreign_keys=[recipient_user_id], back_populates="received_messages")


class Transcript(Base):
    __tablename__ = "transcripts"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    mentor_id = Column(Integer, ForeignKey("mentors.id"), nullable=True)
    storage_uri = Column(String(500))
    summary = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    student = relationship("Student", back_populates="transcripts")
    mentor = relationship("Mentor", back_populates="transcripts")


class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    type = Column(String(100), nullable=False)
    payload = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    student = relationship("Student", back_populates="events")


class Attachment(Base):
    __tablename__ = "attachments"
    
    id = Column(Integer, primary_key=True, index=True)
    owner_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    storage_uri = Column(String(500), nullable=False)
    kind = Column(String(100))
    meta = Column(JSON)
    
    # Relationships
    owner = relationship("User", back_populates="attachments")


class TokenDenylist(Base):
    __tablename__ = "tokens_denylist"
    
    jti = Column(String(255), primary_key=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
