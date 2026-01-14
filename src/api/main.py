import time
import uuid
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from src.api.routes import router
from src.logger import setup_logger
from src.config import settings

logger = setup_logger(__name__)

app = FastAPI(
    title="Zedny Weekly Report API",
    description="Production-grade MVP for Course Recommendations and Weekly Intelligence Reports",
    version="1.1.0"
)

# Application startup state
app.state.start_time = time.time()

@app.middleware("http")
async def add_request_id_and_logging(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    start_time = time.perf_counter()
    
    # Log incoming request
    logger.info({
        "event": "request_start",
        "request_id": request_id,
        "method": request.method,
        "path": request.url.path
    })
    
    response = await call_next(request)
    
    process_time = time.perf_counter() - start_time
    
    # Log outgoing response
    logger.info({
        "event": "request_end",
        "request_id": request_id,
        "status_code": response.status_code,
        "duration_ms": round(process_time * 1000, 2)
    })
    
    response.headers["X-Request-ID"] = request_id
    return response

@app.on_event("startup")
async def startup_event():
    logger.info("Initializing Zedny Report API components...")
    if not settings.check_env():
        logger.critical("Startup failed: Missing environment variables.")
        # In a real production environment, we might raise a SystemExit here

@app.get("/health", tags=["System"])
def health_check():
    """Service health and uptime."""
    uptime = time.time() - app.state.start_time
    return {
        "status": "healthy",
        "version": "1.1.0",
        "uptime_seconds": round(uptime, 2),
        "timestamp": time.time()
    }

@app.get("/", include_in_schema=False)
def root():
    return {
        "service": "Zedny Weekly Report API",
        "status": "running",
        "docs": "/docs",
        "v1": {
            "health": "/health",
            "search": "/recommender/search",
            "role": "/recommender/role",
            "report_json": "/reports/catalog-weekly",
            "report_markdown": "/reports/catalog-weekly/markdown",
            "report_dashboard": "/reports/catalog-weekly/dashboard.png"
        }
    }

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.warning({
        "event": "validation_error",
        "request_id": request_id,
        "errors": exc.errors()
    })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "The request body or parameters are invalid.",
                "request_id": request_id,
                "details": exc.errors()
            }
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(f"Internal error for request {request_id}: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please contact support with the request ID.",
                "request_id": request_id
            }
        }
    )

app.include_router(router)
