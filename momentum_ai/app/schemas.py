from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models import UserRole, PairingStatus, TaskStatus, GoalStatus


# Base schemas
class BaseSchema(BaseModel):
    class Config:
        from_attributes = True


# Auth schemas
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str
    role: UserRole
    school_id: int


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshToken(BaseModel):
    refresh_token: str


# User schemas
class UserBase(BaseSchema):
    id: int
    email: str
    full_name: str
    role: UserRole
    school_id: int
    created_at: datetime


class UserResponse(UserBase):
    pass


# School schemas
class SchoolBase(BaseSchema):
    id: int
    name: str
    district: Optional[str] = None
    created_at: datetime


class SchoolCreate(BaseModel):
    name: str
    district: Optional[str] = None


# Student schemas
class StudentBase(BaseSchema):
    id: int
    user_id: int
    grade_level: Optional[str] = None
    gpa: Optional[float] = None
    risk_score: float = 0.0
    meta: Optional[Dict[str, Any]] = None


class StudentCreate(BaseModel):
    user_id: int
    grade_level: Optional[str] = None
    gpa: Optional[float] = None
    meta: Optional[Dict[str, Any]] = None


class StudentUpdate(BaseModel):
    grade_level: Optional[str] = None
    gpa: Optional[float] = None
    meta: Optional[Dict[str, Any]] = None


class StudentResponse(StudentBase):
    user: UserResponse
    current_plan: Optional[Dict[str, Any]] = None


# Mentor schemas
class MentorBase(BaseSchema):
    id: int
    user_id: int
    capacity: int = 10
    specialties: Optional[List[str]] = None
    meta: Optional[Dict[str, Any]] = None


class MentorCreate(BaseModel):
    user_id: int
    capacity: int = 10
    specialties: Optional[List[str]] = None
    meta: Optional[Dict[str, Any]] = None


class MentorUpdate(BaseModel):
    capacity: Optional[int] = None
    specialties: Optional[List[str]] = None
    meta: Optional[Dict[str, Any]] = None


class MentorResponse(MentorBase):
    user: UserResponse


# Pairing schemas
class PairingBase(BaseSchema):
    id: int
    student_id: int
    mentor_id: int
    status: PairingStatus
    started_at: datetime
    ended_at: Optional[datetime] = None


class PairingCreate(BaseModel):
    student_id: int
    mentor_id: int


class PairingUpdate(BaseModel):
    status: Optional[PairingStatus] = None
    ended_at: Optional[datetime] = None


class PairingResponse(PairingBase):
    student: StudentResponse
    mentor: MentorResponse


# Intervention schemas
class InterventionBase(BaseSchema):
    id: int
    slug: str
    title: str
    category: Optional[str] = None
    description: Optional[str] = None
    protocol: Optional[Dict[str, Any]] = None


class InterventionResponse(InterventionBase):
    pass


# Plan schemas
class PlanBase(BaseSchema):
    id: int
    student_id: int
    created_by: int
    version: int
    active: bool
    plan: Dict[str, Any]
    created_at: datetime


class PlanCreate(BaseModel):
    student_id: int
    plan: Dict[str, Any]


class PlanUpdate(BaseModel):
    plan: Optional[Dict[str, Any]] = None
    active: Optional[bool] = None


class PlanResponse(PlanBase):
    student: StudentResponse
    creator: UserResponse


# Goal schemas
class GoalBase(BaseSchema):
    id: int
    student_id: int
    title: str
    description: Optional[str] = None
    target_date: Optional[datetime] = None
    status: GoalStatus


class GoalCreate(BaseModel):
    student_id: int
    title: str
    description: Optional[str] = None
    target_date: Optional[datetime] = None


class GoalUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    target_date: Optional[datetime] = None
    status: Optional[GoalStatus] = None


class GoalResponse(GoalBase):
    student: StudentResponse


# Task schemas
class TaskBase(BaseSchema):
    id: int
    goal_id: Optional[int] = None
    student_id: int
    title: str
    due_date: Optional[datetime] = None
    status: TaskStatus
    completed_at: Optional[datetime] = None


class TaskCreate(BaseModel):
    goal_id: Optional[int] = None
    student_id: int
    title: str
    due_date: Optional[datetime] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    due_date: Optional[datetime] = None
    status: Optional[TaskStatus] = None
    completed_at: Optional[datetime] = None


class TaskResponse(TaskBase):
    student: StudentResponse
    goal: Optional[GoalResponse] = None


# Checkin schemas
class CheckinBase(BaseSchema):
    id: int
    student_id: int
    mentor_id: Optional[int] = None
    mood: Optional[int] = Field(None, ge=1, le=5)
    obstacles: Optional[List[str]] = None
    notes: Optional[str] = None
    created_at: datetime


class CheckinCreate(BaseModel):
    student_id: int
    mentor_id: Optional[int] = None
    mood: Optional[int] = Field(None, ge=1, le=5)
    obstacles: Optional[List[str]] = None
    notes: Optional[str] = None


class CheckinResponse(CheckinBase):
    student: StudentResponse
    mentor: Optional[MentorResponse] = None


# Message schemas
class MessageBase(BaseSchema):
    id: int
    sender_user_id: int
    recipient_user_id: int
    text: str
    created_at: datetime


class MessageCreate(BaseModel):
    recipient_user_id: int
    text: str


class MessageResponse(MessageBase):
    sender: UserResponse
    recipient: UserResponse


# Transcript schemas
class TranscriptBase(BaseSchema):
    id: int
    student_id: int
    mentor_id: Optional[int] = None
    storage_uri: Optional[str] = None
    summary: Optional[str] = None
    created_at: datetime


class TranscriptResponse(TranscriptBase):
    student: StudentResponse
    mentor: Optional[MentorResponse] = None


# AI schemas
class AITranscribeResponse(BaseModel):
    job_id: str


class AISummarizeRequest(BaseModel):
    transcript_id: int


class AISummarizeResponse(BaseModel):
    summary: str
    action_items: List[str]


class AIPlanRequest(BaseModel):
    student_id: int
    context: str


class AIPlanResponse(BaseModel):
    recommended_items: List[Dict[str, Any]]


# Analytics schemas
class EngagementAnalytics(BaseModel):
    student_id: int
    current_streak: int
    longest_streak: int
    checkin_frequency: float
    task_completion_rate: float


class RiskAnalytics(BaseModel):
    student_id: int
    current_score: float
    trend: List[Dict[str, Any]]
    factors: Dict[str, float]


# WebSocket schemas
class WebSocketMessage(BaseModel):
    type: str
    student_id: Optional[int] = None
    message: Optional[str] = None
    severity: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


# Error schemas
class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


# Pagination schemas
class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int


# Search schemas
class StudentSearch(BaseModel):
    search: Optional[str] = None
    page: int = 1
    size: int = 20
