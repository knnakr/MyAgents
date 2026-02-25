"""
FastAPI Backend for Career Assistant AI Agent
RESTful API endpoints for processing employer messages and managing the agent
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, List
from datetime import datetime
import json
import os

from career_assistant import CareerAssistant

# Initialize FastAPI app
app = FastAPI(
    title="Career Assistant API",
    description="AI-powered career communication assistant with quality control",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Career Assistant
assistant = CareerAssistant()

# ==================== REQUEST/RESPONSE MODELS ====================

class EmployerMessage(BaseModel):
    employer_name: str
    employer_email: Optional[EmailStr] = None
    message: str
    company: Optional[str] = None

class ProcessMessageResponse(BaseModel):
    employer_message: str
    generated_response: str
    evaluation: Dict
    status: str
    revision_count: int
    timestamp: str

class EvaluationRequest(BaseModel):
    employer_message: str
    generated_response: str

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    model: str

class LogsResponse(BaseModel):
    log_type: str
    entries: List[Dict]
    count: int

# ==================== API ENDPOINTS ====================

@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "model": "Groq Llama 3.3 70B"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "model": assistant.model
    }

@app.post("/api/process-message", response_model=ProcessMessageResponse)
async def process_message(message: EmployerMessage, background_tasks: BackgroundTasks):
    """
    Process an employer message and generate a response
    
    - **employer_name**: Name of the employer/recruiter
    - **message**: The message content from employer
    - **employer_email**: Optional email for contact record
    - **company**: Optional company name
    """
    try:
        # Process the message
        result = assistant.process_employer_message(
            employer_message=message.message,
            employer_name=message.employer_name
        )
        
        # If email provided, it will be recorded via tool calling
        # This is handled automatically by the agent
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

@app.post("/api/evaluate")
async def evaluate_response(request: EvaluationRequest):
    """
    Evaluate a response without processing entire message flow
    Useful for testing different responses
    """
    try:
        evaluation = assistant.evaluate_response(
            employer_message=request.employer_message,
            generated_response=request.generated_response
        )
        
        return {
            "evaluation": evaluation,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation error: {str(e)}")

@app.get("/api/logs/{log_type}", response_model=LogsResponse)
async def get_logs(log_type: str, limit: int = 10):
    """
    Retrieve logs by type
    
    - **log_type**: evaluation, employer_contacts, interviews, unknown_questions, declined_offers
    - **limit**: Number of recent entries to return (default: 10)
    """
    valid_types = {
        "evaluation": "evaluation_logs.log",
        "employer_contacts": "employer_contacts.log",
        "interviews": "interviews.log",
        "unknown_questions": "unknown_questions.log",
        "declined_offers": "declined_offers.log"
    }
    
    if log_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid log type. Must be one of: {', '.join(valid_types.keys())}"
        )
    
    log_file = valid_types[log_type]
    
    try:
        if not os.path.exists(log_file):
            return {
                "log_type": log_type,
                "entries": [],
                "count": 0
            }
        
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        # Parse JSON entries
        entries = []
        for line in reversed(lines[-limit:]):  # Get last N entries
            try:
                entries.append(json.loads(line.strip()))
            except json.JSONDecodeError:
                continue
        
        return {
            "log_type": log_type,
            "entries": entries,
            "count": len(entries)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading logs: {str(e)}")

@app.get("/api/stats")
async def get_statistics():
    """
    Get overall statistics from evaluation logs
    """
    try:
        if not os.path.exists("evaluation_logs.log"):
            return {
                "total_messages": 0,
                "avg_score": 0,
                "approval_rate": 0,
                "avg_revisions": 0
            }
        
        with open("evaluation_logs.log", "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        total = 0
        scores = []
        approved = 0
        revisions = []
        
        for line in lines:
            try:
                entry = json.loads(line.strip())
                total += 1
                scores.append(entry.get("evaluation_scores", {}).get("overall_score", 0))
                if entry.get("status") == "approved_and_sent":
                    approved += 1
                revisions.append(entry.get("revision_count", 0))
            except json.JSONDecodeError:
                continue
        
        return {
            "total_messages": total,
            "avg_score": round(sum(scores) / len(scores), 2) if scores else 0,
            "approval_rate": round((approved / total) * 100, 1) if total > 0 else 0,
            "avg_revisions": round(sum(revisions) / len(revisions), 2) if revisions else 0,
            "score_distribution": {
                "excellent (9-10)": len([s for s in scores if s >= 9]),
                "good (8-9)": len([s for s in scores if 8 <= s < 9]),
                "acceptable (7-8)": len([s for s in scores if 7 <= s < 8]),
                "needs_improvement (<7)": len([s for s in scores if s < 7])
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating stats: {str(e)}")

@app.delete("/api/logs/{log_type}")
async def clear_logs(log_type: str):
    """
    Clear specific log file (use with caution)
    """
    valid_types = {
        "evaluation": "evaluation_logs.log",
        "employer_contacts": "employer_contacts.log",
        "interviews": "interviews.log",
        "unknown_questions": "unknown_questions.log",
        "declined_offers": "declined_offers.log"
    }
    
    if log_type not in valid_types:
        raise HTTPException(status_code=400, detail="Invalid log type")
    
    log_file = valid_types[log_type]
    
    try:
        if os.path.exists(log_file):
            os.remove(log_file)
        return {"message": f"{log_type} logs cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing logs: {str(e)}")

# ==================== RUN SERVER ====================

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Career Assistant API Server...")
    print("📚 API Documentation: http://127.0.0.1:8000/docs")
    print("📊 Interactive API: http://127.0.0.1:8000/redoc")
    
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
