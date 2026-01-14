import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

from pydantic import field_validator, Field, AliasChoices

class Settings(BaseSettings):
    # Project Root
    ROOT_DIR: Path = Path(__file__).parent.parent.absolute()

    # Data Paths
    DATA_DIR: Path = ROOT_DIR / "data"
    COURSES_CSV: Path = DATA_DIR / "courses.csv"
    CLEAN_DATA_PARQUET: Path = DATA_DIR / "courses_clean.parquet"
    FAISS_INDEX_PATH: Path = DATA_DIR / "faiss.index"
    EMBEDDINGS_PATH: Path = DATA_DIR / "course_embeddings.npy"

    # Models
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    RERANKER_MODEL_NAME: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # Validation & Thresholds
    MIN_QUERY_LENGTH: int = 2
    SEMANTIC_THRESHOLD_ARABIC: float = 0.25
    SEMANTIC_THRESHOLD_GENERAL: float = 0.35
    SEMANTIC_THRESHOLD_RELAXED: float = 0.22
    TOP_K_DEFAULT: int = 10
    TOP_K_Candidates: int = 100

    # Zedny API Settings
    ZEDNY_BASE_URL: str = Field(..., validation_alias=AliasChoices("ZEDNY_BASE_URL", "ZEDNY_URL"))
    ZEDNY_AUTH_TOKEN: str = Field(..., validation_alias=AliasChoices("ZEDNY_AUTH_TOKEN", "ZEDNY_TOKEN"))
    ZEDNY_LANG: str = "en"
    LOG_LEVEL: str = "INFO"

    # SMTP / Email Settings
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: str = "noreply@zedny.ai"
    EMAIL_TO: Optional[str] = None
    EMAIL_SUBJECT: str = "Zedny Weekly Catalog Report"

    # Scraper & Reports
    COMPANY_BASE_URL: str = Field("https://zedny.ai", validation_alias=AliasChoices("COMPANY_BASE_URL", "BASE_URL"))
    COMPANY_REFERRER: str = Field("https://zedny.ai/", validation_alias=AliasChoices("COMPANY_REFERRER", "REFERRER"))
    COURSE_BASE_URL: str = Field("https://zedny.com/course", validation_alias=AliasChoices("COURSE_BASE_URL", "COURSE_URL"))
    REPORT_OUTPUT_DIR: Path = ROOT_DIR / "outputs"
    HEADLESS: bool = True
    REQUEST_TIMEOUT: int = 30
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    @field_validator("ZEDNY_AUTH_TOKEN")
    @classmethod
    def token_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("ZEDNY_AUTH_TOKEN is missing! Please provide it in .env")
        return v.strip()

    def check_env(self):
        """Perform startup checks to ensure critical environment variables are set."""
        critical_vars = ["ZEDNY_BASE_URL", "ZEDNY_AUTH_TOKEN", "COMPANY_BASE_URL"]
        missing = []
        for var in critical_vars:
            if not getattr(self, var):
                missing.append(var)
        
        if missing:
            print(f"CRITICAL ERROR: The following environment variables are missing: {', '.join(missing)}")
            print("Please check your .env file or environment variables.")
            return False
        return True

    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
# Execute baseline check
if not settings.check_env():
    # In a real production app, we might exit(1) here.
    # For this refactor, we'll just log or print a warning.
    pass
