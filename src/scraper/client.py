import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from src.config import settings
from src.logger import setup_logger

logger = setup_logger(__name__)

class ZednyClientError(Exception):
    def __init__(self, message: str, status_code: int = None, endpoint: str = None, response_body: str = None):
        super().__init__(message)
        self.status_code = status_code
        self.endpoint = endpoint
        self.response_body = response_body

class ZednyClient:
    def __init__(self, base_url: str = None, token: str = None):
        self.base_url = (base_url or settings.ZEDNY_BASE_URL).rstrip("/")
        self.token = token or settings.ZEDNY_AUTH_TOKEN
        
        if not self.token:
            raise ValueError("Zedny Token is missing. Ensure ZEDNY_AUTH_TOKEN is set in .env")

        self.session = requests.Session()
        
        # Configure Retries
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Professional Headers matching company behavior
        auth_header = self.token if self.token.lower().startswith("bearer ") else f"Bearer {self.token}"
        self.session.headers.update({
            "Authorization": auth_header,
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Accept-Language": "en",
            "x-language": settings.ZEDNY_LANG,
            "DNT": "1",
            "Origin": settings.COMPANY_BASE_URL,
            "Referer": settings.COMPANY_REFERRER,
            "User-Agent": settings.USER_AGENT
        })

    def _get(self, endpoint: str, params: dict = None) -> dict:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            # Set a clear timeout of 10 seconds per request
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 401:
                logger.error(f"Unauthorized (401) at {endpoint}. Token likely expired.")
                raise ZednyClientError("Unauthorized (401). Token expired or invalid.", 
                                       status_code=401, endpoint=endpoint, response_body=response.text)
            
            response.raise_for_status()
            return response.json()
            
        except ZednyClientError:
            raise
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response is not None else 500
            error_body = e.response.text if e.response is not None else str(e)
            logger.error(f"API HTTPError: {status_code} at {endpoint} - {error_body}")
            raise ZednyClientError(f"API request failed: {str(e)}", 
                                   status_code=status_code, endpoint=endpoint, response_body=error_body)
        except requests.exceptions.Timeout:
            logger.error(f"API Timeout at {endpoint}")
            raise ZednyClientError("API request timed out", status_code=504, endpoint=endpoint)
        except Exception as e:
            logger.error(f"Unexpected error calling API {endpoint}: {str(e)}")
            raise ZednyClientError(f"Unexpected error: {str(e)}", endpoint=endpoint)

    def get_categories(self, product_type: int = 3) -> list[dict]:
        """Fetch course categories."""
        data = self._get("products/categories", params={"product_type": product_type})
        return data.get("results", [])

    def get_courses(self, page: int = 1, limit: int = 50) -> dict:
        """Fetch all courses with pagination."""
        return self._get("courses/all", params={"page": page, "limit": limit})

    def get_all_courses(self, limit: int = 50, max_pages: int = 50) -> list[dict]:
        """Fetch all courses by looping through pages."""
        all_courses = []
        page = 1
        total = 0
        
        logger.info(f"Starting to fetch all courses (limit={limit}, max_pages={max_pages})")
        
        while page <= max_pages:
            try:
                data = self.get_courses(page=page, limit=limit)
                results = data.get("results", []) or data.get("products", [])
                total = data.get("total", 0)
                
                if not results:
                    break
                    
                all_courses.extend(results)
                if len(all_courses) >= total or not total:
                    break
                    
                page += 1
            except Exception as e:
                logger.error(f"Pagination failed at page {page}: {str(e)}")
                raise
                
        logger.info(f"Successfully fetched {len(all_courses)} courses total.")
        return all_courses
