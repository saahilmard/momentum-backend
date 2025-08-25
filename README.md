[README.md](https://github.com/user-attachments/files/21959592/README.md)
# Momentum AI - Academic Recovery Platform

An AI-assisted academic recovery platform that reduces "academic spirals" after setbacks through mentor pairing, micro-interventions, and steady progress tracking.

## 🎯 Problem & Solution

**Problem**: After a bad grade or missed deadlines, many students enter a shame/avoidance loop (an "academic spiral"): disengagement → more missed work → worse outcomes. Schools have limited counselor bandwidth; interventions often arrive late.

**Solution**: Pair each student with a mentor and a personalized, low-friction plan (SMART goals + micro-tasks + brief check-ins). A lightweight risk score spots spirals early. Interventions are evidence-informed and AI-assisted.

## 🏗️ Architecture

- **Backend**: FastAPI + SQLAlchemy 2.0 + PostgreSQL 15
- **Authentication**: JWT with Argon2 password hashing
- **Real-time**: WebSocket for alerts and notifications
- **Background Jobs**: RQ for risk scoring and AI processing
- **Observability**: Structured logging + Prometheus metrics
- **Containerization**: Docker + docker-compose

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd momentum_ai
```

### 2. Environment Setup

Create a `.env` file:

```bash
# Database
DATABASE_URL=postgresql://momentum:momentum@localhost:5432/momentum
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
```

### 3. Start Services

```bash
# Start all services
make up

# Or manually:
docker-compose up -d
```

### 4. Initialize Database

```bash
# Run migrations
make migrate

# Seed with demo data
make seed
```

### 5. Access the API

- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/healthz
- **Metrics**: http://localhost:8000/metrics

## 📊 Demo Data

The seeding script creates:

- 1 demo school
- 1 admin user
- 5 mentor users with specialties
- 20 student users with varied profiles
- 10 evidence-based interventions
- Sample goals, tasks, and check-ins

### Demo Login Credentials

```
Admin:    admin@demo.com / admin123
Mentor:   mentor1@demo.com / mentor123
Student:  student1@demo.com / student123
```

## 🔧 Development

### Available Commands

```bash
# Start services
make up

# Stop services
make down

# Run migrations
make migrate

# Seed database
make seed

# Run tests
make test

# Lint code
make lint

# Format code
make format

# Reset database (drop + recreate + seed)
make db-reset

# View logs
make logs

# Run risk scoring job
make risk-score
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set up pre-commit hooks
pre-commit install

# Run tests
pytest -v --cov=app

# Start development server
uvicorn app.main:app --reload
```

## 📚 API Documentation

### Authentication

All endpoints require authentication via JWT Bearer token (except `/auth/register` and `/auth/login`).

```bash
# Register
POST /api/v1/auth/register
{
  "email": "user@example.com",
  "password": "securepassword",
  "full_name": "John Doe",
  "role": "student",
  "school_id": 1
}

# Login
POST /api/v1/auth/login
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

### Core Endpoints

#### Students
- `GET /api/v1/students` - List students (paginated)
- `POST /api/v1/students` - Create student
- `GET /api/v1/students/{id}` - Get student details
- `PATCH /api/v1/students/{id}` - Update student

#### Mentors
- `GET /api/v1/mentors` - List mentors
- `POST /api/v1/mentors` - Create mentor
- `GET /api/v1/mentors/{id}` - Get mentor details

#### Plans & Interventions
- `GET /api/v1/plans/interventions` - List available interventions
- `POST /api/v1/plans` - Create plan for student
- `GET /api/v1/plans/{id}` - Get plan details
- `POST /api/v1/plans/{id}/activate` - Activate plan

#### Goals & Tasks
- `POST /api/v1/goals` - Create goal
- `PATCH /api/v1/goals/{id}` - Update goal
- `POST /api/v1/tasks` - Create task
- `PATCH /api/v1/tasks/{id}` - Update task

#### Check-ins & Communication
- `POST /api/v1/checkins` - Create check-in
- `GET /api/v1/checkins` - List check-ins
- `POST /api/v1/messages` - Send message

#### AI Services
- `POST /api/v1/ai/transcribe` - Upload audio for transcription
- `POST /api/v1/ai/summarize` - Summarize transcript
- `POST /api/v1/ai/plan` - Get AI plan recommendations

#### Analytics
- `GET /api/v1/analytics/engagement` - Get engagement metrics
- `GET /api/v1/analytics/risk` - Get risk analytics

#### Real-time
- `GET /api/v1/ws?token=...` - WebSocket for real-time alerts

## 🧠 Risk Scoring

The platform uses a sophisticated risk scoring algorithm that considers:

- **Overdue Load** (30%): Fraction of open tasks overdue
- **Mood Trend** (20%): Change in average mood vs prior period
- **Streak** (15%): Days with completed tasks
- **Engagement** (15%): Days since last check-in
- **Goal Velocity** (10%): % of goals completed on time
- **GPA Trend** (10%): Academic performance trajectory

Risk levels:
- **Low**: < 0.33
- **Medium**: 0.33 - 0.66
- **High**: > 0.66

High-risk students trigger real-time alerts to assigned mentors.

## 🎯 Interventions

The platform includes 10 evidence-based interventions:

1. **Timeboxing** - Daily time-block planning
2. **Spaced Repetition** - 20-min focused study blocks
3. **CBT Thought Reframing** - Cognitive behavioral techniques
4. **Sleep Regularity** - Consistent sleep schedule
5. **5-Minute Activation** - Procrastination busting
6. **Pomodoro Technique** - Focus cycles
7. **Backward Planning** - Deadline management
8. **Accountability Pings** - Daily mentor check-ins
9. **Weekly Reflection** - Progress review
10. **Exam Warmups** - Retrieval practice

## 🔒 Security & Privacy

- **Authentication**: JWT with refresh token rotation
- **Password Hashing**: Argon2 (industry standard)
- **Authorization**: Role-based access control (RBAC)
- **Data Privacy**: School-scoped data isolation
- **Audit Trail**: Complete event logging
- **Token Security**: Denylist for revoked tokens

## 📈 Monitoring & Observability

- **Health Checks**: `/healthz` endpoint
- **Metrics**: Prometheus format at `/metrics`
- **Logging**: Structured JSON logs
- **Error Handling**: Consistent error responses
- **Performance**: Request/response timing

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run with verbose output
pytest -v
```

## 🚀 Deployment

### Production Checklist

- [ ] Update `SECRET_KEY` to strong random value
- [ ] Configure production database
- [ ] Set up SSL/TLS certificates
- [ ] Configure proper CORS origins
- [ ] Set up monitoring and alerting
- [ ] Configure backup strategy
- [ ] Set up CI/CD pipeline

### Environment Variables

```bash
# Required
DATABASE_URL=postgresql://user:pass@host:port/db
REDIS_URL=redis://host:port/db
SECRET_KEY=your-super-secret-key

# Optional
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
CORS_ORIGINS=["https://yourdomain.com"]
STORAGE_PATH=/app/storage
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run linting and tests
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:

- Create an issue in the repository
- Check the API documentation at `/docs`
- Review the health check at `/healthz`

---

**Built with ❤️ for students, mentors, and educators** 
