from fastapi import APIRouter, HTTPException, Depends, Response
from typing import List, Optional
import logging
from datetime import datetime, timezone

from src.ai.pipeline import CourseRecommenderPipeline
from src.api.schemas import (
    SearchRequest, SearchResponse, RoleRequest, RoleResponse, CourseResponse,
    WeeklyCatalogReportV2, MarkdownReportResponse
)
from src.api.filters import ROLE_FILTERS, apply_filters
from src.report.catalog_weekly import build_catalog_weekly_report
from src.report.catalog_weekly_dashboard import build_weekly_bi_dashboard

logger = logging.getLogger(__name__)
router = APIRouter()

# Global pipeline instance (Lazy loaded as requested by some configs, but pipeline init is usually at startup)
_pipeline = None

def get_pipeline():
    global _pipeline
    if _pipeline is None:
        try:
            _pipeline = CourseRecommenderPipeline()
        except Exception as e:
            logger.error(f"Failed to initialize recommender pipeline: {e}")
            raise RuntimeError("Recommender engine failed to start")
    return _pipeline

@router.post("/recommender/search", response_model=SearchResponse)
async def semantic_search(request: SearchRequest, pipeline: CourseRecommenderPipeline = Depends(get_pipeline)):
    """Semantic search based on user query."""
    try:
        # Map SearchRequest to pipeline's RecommendRequest (if they differ slightly)
        from src.schemas import RecommendRequest
        pipe_req = RecommendRequest(
            query=request.query,
            top_k=request.top_k,
            enable_reranking=True
        )
        result = pipeline.recommend(pipe_req)
        
        # Map pipeline Recommendation objects to CourseResponse
        courses = [
            CourseResponse(
                title=r.title,
                url=r.url,
                category=r.category,
                level=r.level,
                rank=r.rank,
                score=r.score,
                why=r.why
            ) for r in result.results
        ]
        
        return SearchResponse(
            results=courses,
            total_found=len(courses),
            debug_info=result.debug_info
        )
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/recommender/role", response_model=RoleResponse)
async def role_recommendation(request: RoleRequest, pipeline: CourseRecommenderPipeline = Depends(get_pipeline)):
    """Role-aware course recommendations with strict filtering."""
    try:
        # Get defaults for role if not provided
        role_defaults = ROLE_FILTERS.get(request.role, {})
        allowed_cats = request.allowed_categories or role_defaults.get("allowed_categories")
        exclude_kws = request.exclude_keywords or role_defaults.get("exclude_keywords")

        from src.schemas import RecommendRequest
        pipe_req = RecommendRequest(
            query=request.role,
            top_k=50, # Get more candidates to allow for filtering
            enable_reranking=True
        )
        
        raw_result = pipeline.recommend(pipe_req)
        
        # Convert to dict for filter processing
        raw_list = [r.dict() for r in raw_result.results]
        
        # Apply filters
        filtered_list = apply_filters(
            raw_list, 
            allowed_categories=allowed_cats, 
            exclude_keywords=exclude_kws
        )
        
        # Map to final response
        courses = [CourseResponse(**c) for c in filtered_list[:request.top_k]]
        
        return RoleResponse(
            role=request.role,
            top_k=request.top_k,
            results=courses,
            filtered_out=len(raw_list) - len(filtered_list),
            applied_filters={
                "allowed_categories": allowed_cats,
                "exclude_keywords": exclude_kws
            }
        )
    except Exception as e:
        logger.error(f"Role recommendation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reports/catalog-weekly", response_model=WeeklyCatalogReportV2)
async def get_catalog_weekly_report():
    """Returns the full weekly catalog report as JSON."""
    try:
        report = build_catalog_weekly_report()
        return report
    except Exception as e:
        logger.error(f"Catalog report error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate weekly report")

@router.get("/reports/catalog-weekly/markdown", response_model=MarkdownReportResponse)
async def get_catalog_weekly_markdown():
    """Returns the weekly catalog report in Markdown format."""
    try:
        report = build_catalog_weekly_report()
        return MarkdownReportResponse(markdown=report.get("markdown_summary", ""))
    except Exception as e:
        logger.error(f"Catalog markdown error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate markdown report")

@router.get("/reports/catalog-weekly/dashboard.png")
async def get_catalog_weekly_dashboard():
    """Returns a BI-style dashboard PNG image."""
    try:
        report = build_catalog_weekly_report()
        img_bytes = build_weekly_bi_dashboard(report)
        return Response(content=img_bytes, media_type="image/png")
    except Exception as e:
        logger.error(f"Dashboard generation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate dashboard image")

@router.get("/reports/catalog-weekly/html")
async def get_catalog_weekly_report_html(top_n: int = 10, bottom_n: int = 10):
    """Returns the weekly catalog report as a clean HTML dashboard."""
    try:
        from src.report.pdf_renderer import render_catalog_weekly_html
        report = build_catalog_weekly_report(top_n=top_n, bottom_n=bottom_n)
        html_content = render_catalog_weekly_html(report)
        return Response(content=html_content, media_type="text/html")
    except Exception as e:
        logger.error(f"HTML report error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate HTML report: {str(e)}")

@router.get("/reports/catalog-weekly/pdf")
async def get_catalog_weekly_report_pdf(top_n: int = 10, bottom_n: int = 10):
    """Returns the weekly catalog report as a professional PDF Dashboard."""
    try:
        from src.report.pdf_renderer import render_catalog_weekly_html, html_to_pdf
        report = build_catalog_weekly_report(top_n=top_n, bottom_n=bottom_n)
        html_content = render_catalog_weekly_html(report)
        pdf_bytes = await html_to_pdf(html_content)
        
        filename = f"Zedny_Weekly_Report_{datetime.now(timezone.utc).strftime('%Y%m%d')}.pdf"
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except Exception as e:
        logger.error(f"PDF report error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF report: {str(e)}")
