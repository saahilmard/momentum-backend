from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import prometheus_client
from prometheus_client import Counter, Histogram
import time

from app.config import settings
from app.database import engine, Base
from app.models import *  # Import all models for Alembic
from app.websocket_manager import manager

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency')

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Momentum AI backend")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    yield
    
    # Shutdown
    logger.info("Shutting down Momentum AI backend")

# Create FastAPI app
app = FastAPI(
    title="Momentum AI",
    description="AI-assisted academic recovery platform",
    version="1.0.0",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure appropriately for production
)

# Request/Response middleware for metrics and logging
@app.middleware("http")
async def metrics_middleware(request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    # Record metrics
    duration = time.time() - start_time
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    REQUEST_LATENCY.observe(duration)
    
    # Log request
    logger.info(
        f"HTTP request - {request.method} {request.url.path} - {response.status_code} - {duration:.3f}s"
    )
    
    return response

# Error handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(
        "Unhandled exception",
        exc_info=exc,
        path=request.url.path,
        method=request.method
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal server error occurred",
                "details": {}
            }
        }
    )

# Health check endpoint
@app.get("/healthz")
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    return prometheus_client.generate_latest()

# WebSocket endpoint
@app.websocket("/api/v1/ws")
async def websocket_endpoint(websocket: WebSocket):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return
    
    user_id = await manager.connect(websocket, token)
    if not user_id:
        return
    
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            # Echo back for testing
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)

# Import and include routers
from app.routers import auth, students, mentors, plans, goals, tasks, checkins, messages, ai, analytics

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(students.router, prefix="/api/v1/students", tags=["Students"])
app.include_router(mentors.router, prefix="/api/v1/mentors", tags=["Mentors"])
app.include_router(plans.router, prefix="/api/v1/plans", tags=["Plans"])
app.include_router(goals.router, prefix="/api/v1/goals", tags=["Goals"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["Tasks"])
app.include_router(checkins.router, prefix="/api/v1/checkins", tags=["Check-ins"])
app.include_router(messages.router, prefix="/api/v1/messages", tags=["Messages"])
app.include_router(ai.router, prefix="/api/v1/ai", tags=["AI Services"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Momentum AI Backend",
        "version": "1.0.0",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }
