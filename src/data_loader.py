try:
    import faiss
    import pandas as pd
    HAS_DATA_LIBS = True
except ImportError:
    HAS_DATA_LIBS = False

import numpy as np
from typing import Tuple, Optional, Any
from src.config import settings
from src.logger import setup_logger

logger = setup_logger(__name__)

class DataLoader:
    _instance = None
    _index = None
    _courses_df = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DataLoader, cls).__new__(cls)
        return cls._instance

    def load_data(self) -> Tuple[Optional[Any], Optional[Any]]:
        """Load FAISS index and Courses DataFrame."""
        if not HAS_DATA_LIBS:
            logger.warning("Data libraries (faiss/pandas) not found. Recommendation features disabled.")
            return None, None

        if self._index is not None and self._courses_df is not None:
            return self._index, self._courses_df
            
        try:
            logger.info("Loading FAISS index...")
            if not settings.FAISS_INDEX_PATH.exists():
                logger.error(f"FAISS index not found at {settings.FAISS_INDEX_PATH}")
                return None, None
                
            self._index = faiss.read_index(str(settings.FAISS_INDEX_PATH))
            
            logger.info("Loading Courses Parquet...")
            if not settings.CLEAN_DATA_PARQUET.exists():
                logger.error(f"Data not found at {settings.CLEAN_DATA_PARQUET}")
                return None, None
                
            self._courses_df = pd.read_parquet(settings.CLEAN_DATA_PARQUET)
            
            logger.info("Data loaded successfully.")
            return self._index, self._courses_df
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return None, None
