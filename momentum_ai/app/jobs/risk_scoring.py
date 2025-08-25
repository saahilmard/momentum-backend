#!/usr/bin/env python3
"""
Risk scoring background job for Momentum AI.
Calculates risk scores for all students and sends alerts for high-risk students.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Student
from app.risk_scoring import RiskScoringEngine
from app.websocket_manager import manager
import structlog
import asyncio

logger = structlog.get_logger()

def run_risk_scoring():
    """Run risk scoring for all students."""
    db = SessionLocal()
    
    try:
        logger.info("Starting risk scoring job")
        
        # Get all students
        students = db.query(Student).all()
        logger.info(f"Processing {len(students)} students")
        
        risk_engine = RiskScoringEngine(db)
        high_risk_students = []
        
        for student in students:
            try:
                # Calculate risk score
                risk_data = risk_engine.update_student_risk_score(student.id)
                
                # Check if student is high risk
                if risk_data['severity'] == 'high':
                    high_risk_students.append({
                        'student_id': student.id,
                        'risk_score': risk_data['risk_score'],
                        'user_name': student.user.full_name
                    })
                
                logger.info(
                    "Student risk score updated",
                    student_id=student.id,
                    risk_score=risk_data['risk_score'],
                    severity=risk_data['severity']
                )
                
            except Exception as e:
                logger.error(
                    "Error calculating risk score for student",
                    student_id=student.id,
                    error=str(e)
                )
        
        # Send alerts for high-risk students
        if high_risk_students:
            logger.info(f"Sending alerts for {len(high_risk_students)} high-risk students")
            
            # In a real implementation, you would send WebSocket alerts here
            # For now, just log them
            for student_data in high_risk_students:
                logger.warning(
                    "High-risk student detected",
                    student_id=student_data['student_id'],
                    risk_score=student_data['risk_score'],
                    user_name=student_data['user_name']
                )
        
        logger.info("Risk scoring job completed successfully")
        
    except Exception as e:
        logger.error(f"Error in risk scoring job: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    run_risk_scoring()
