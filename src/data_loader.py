import faiss
import pandas as pd
import numpy as np
from typing import Tuple, Optional
from src.config import FAISS_INDEX_PATH, CLEAN_DATA_PARQUET, EMBEDDINGS_PATH
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

    def load_data(self) -> Tuple[Optional[faiss.Index], Optional[pd.DataFrame]]:
        """Load FAISS index and Courses DataFrame."""
        if self._index is not None and self._courses_df is not None:
            return self._index, self._courses_df
            
        try:
            logger.info("Loading FAISS index...")
            if not FAISS_INDEX_PATH.exists():
                logger.error(f"FAISS index not found at {FAISS_INDEX_PATH}")
                return None, None
                
            self._index = faiss.read_index(str(FAISS_INDEX_PATH))
            
            logger.info("Loading Courses Parquet...")
            if not CLEAN_DATA_PARQUET.exists():
                logger.error(f"Data not found at {CLEAN_DATA_PARQUET}")
                return None, None
                
            self._courses_df = pd.read_parquet(CLEAN_DATA_PARQUET)
            
            logger.info("Data loaded successfully.")
            return self._index, self._courses_df
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise
