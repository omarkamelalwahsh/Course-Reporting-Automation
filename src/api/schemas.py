from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None

class ErrorResponse(BaseModel):
    error: ErrorDetail

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query")
    top_k: int = Field(5, ge=1, le=50, description="Number of recommendations to return")

    @validator('query')
    def query_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Query cannot be empty or only whitespace")
        return v

class RoleRequest(BaseModel):
    role: str = Field(..., min_length=1, description="User role (e.g., Data Analyst)")
    top_k: int = Field(5, ge=1, le=50)
    allowed_categories: Optional[List[str]] = Field(None, description="Categories to include")
    exclude_keywords: Optional[List[str]] = Field(None, description="Keywords to exclude from results")

    @validator('role')
    def role_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Role cannot be empty or only whitespace")
        return v

class CourseResponse(BaseModel):
    title: str
    url: str
    category: str
    level: str
    rank: int
    score: float
    why: List[str]

class RoleResponse(BaseModel):
    role: str
    top_k: int
    results: List[CourseResponse]
    filtered_out: int
    applied_filters: Dict[str, Any]

class SearchResponse(BaseModel):
    results: List[CourseResponse]
    total_found: int
    debug_info: Optional[Dict[str, Any]] = None

class WeeklyProgress(BaseModel):
    week: str
    courses_completed: int
    hours_learned: float
    status: str
    streak_days: int

class HealthResponse(BaseModel):
    status: str
    version: str
    uptime: float

class CategoryStats(BaseModel):
    id: str
    name: str
    product_count: int
    share: float

class WeeklyCatalogKPIs(BaseModel):
    total_categories: int
    total_courses: int

class PromotedItem(BaseModel):
    title: str
    url: str = "#"
    category: str = "General"
    level: str = "All Levels"

class WeeklyCatalogReport(BaseModel):
    generated_at: str
    kpis: Dict[str, Any]
    categories: List[Dict[str, Any]]
    top_categories: List[Dict[str, Any]]
    low_coverage_categories: List[Dict[str, Any]]
    featured: List[PromotedItem] = []
    top_sliders: List[PromotedItem] = []
    insights: List[str]
    markdown_summary: str

# --- V2 Report Schemas ---

class LevelStats(BaseModel):
    level: str
    count: int
    share: float

class CategoryCourseStats(BaseModel):
    id: str
    name: str
    course_count: int
    share: float

class InstructorStats(BaseModel):
    id: str
    name: str
    course_count: int

class WeeklyCatalogKPIsV2(BaseModel):
    total_courses: int
    total_categories: int
    total_instructors: int

class WeeklyCatalogReportV2(BaseModel):
    generated_at: str
    data_source: str = "zedny_api"
    kpis: WeeklyCatalogKPIsV2
    levels_distribution: List[LevelStats]
    categories: List[CategoryCourseStats]
    top_categories: List[CategoryCourseStats]
    low_coverage_categories: List[CategoryCourseStats]
    top_instructors: List[InstructorStats]
    featured: List[PromotedItem] = []
    top_sliders: List[PromotedItem] = []
    insights: List[str]
    markdown_summary: str
    chart_data: Dict[str, List]

class MarkdownReportResponse(BaseModel):
    markdown: str

class ZednyDebugResponse(BaseModel):
    endpoint: str
    status: str
    count: int
    sample: List[Dict[str, Any]]

class ZednyCoursesDebugResponse(BaseModel):
    endpoint: str
    status: str
    total: int
    count: int
    results: List[Dict[str, Any]]
