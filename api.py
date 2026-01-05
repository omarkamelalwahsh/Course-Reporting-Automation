"""
FastAPI endpoint for Course Recommender System.
Ready for integration with n8n or other automation tools.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime
import uvicorn

from src.recommender import CourseRecommender

# Initialize FastAPI app
app = FastAPI(
    title="Zedny Course Recommender API",
    description="AI-Powered Course Recommendation System using Semantic Embeddings",
    version="1.0.0"
)

# Initialize recommender (singleton)
recommender = None

def get_recommender():
    """Get or initialize the recommender instance."""
    global recommender
    if recommender is None:
        recommender = CourseRecommender()
        recommender.load_courses("data/courses.csv")
    return recommender


# Request/Response Models
class RecommendRequest(BaseModel):
    """Request model for course recommendations."""
    user_interest: str = Field(..., min_length=3, description="Users learning interest or query")
    top_k: int = Field(default=30, ge=1, le=50, description="Number of recommendations to return")


class CourseRecommendation(BaseModel):
    """Model for a single course recommendation."""
    course_id: int
    title: str
    category: str
    level: str
    duration_hours: float
    skills: str
    rank: int


class RecommendResponse(BaseModel):
    """Response model for course recommendations."""
    timestamp: str
    user_interest: str
    total_results: int
    recommendations: List[CourseRecommendation]


# API Endpoints
@app.get("/")
def root():
    """Root endpoint with API information."""
    return {
        "message": "Zedny Course Recommender API",
        "version": "1.0.0",
        "endpoints": {
            "POST /recommend": "Get course recommendations based on user interest",
            "GET /health": "Health check endpoint"
        }
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    try:
        rec = get_recommender()
        return {
            "status": "healthy",
            "total_courses": len(rec.courses_df) if rec.courses_df is not None else 0,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Service unhealthy: {str(e)}")


@app.post("/recommend", response_model=RecommendResponse)
def recommend_courses(request: RecommendRequest):
    """Get course recommendations based on user interest."""
    if not request.user_interest or len(request.user_interest.strip()) < 3:
        raise HTTPException(
            status_code=400,
            detail="user_interest must be at least 3 characters long"
        )
    
    try:
        rec = get_recommender()
        recommendations = rec.recommend(
            user_query=request.user_interest.strip(),
            top_k=request.top_k
        )
        
        course_recommendations = [
            CourseRecommendation(
                course_id=r["course_id"],
                title=r["title"],
                category=r["category"],
                level=r["level"],
                duration_hours=r["duration_hours"],
                skills=r["skills"],
                rank=r["rank"]
            )
            for r in recommendations
        ]
        
        return RecommendResponse(
            timestamp=datetime.now().isoformat(),
            user_interest=request.user_interest.strip(),
            total_results=len(course_recommendations),
            recommendations=course_recommendations
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating recommendations: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
