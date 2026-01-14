try:
    from sentence_transformers import SentenceTransformer, CrossEncoder
    HAS_ML = True
except ImportError:
    HAS_ML = False

import numpy as np
from typing import List, Union
from src.config import settings
from src.logger import setup_logger

logger = setup_logger(__name__)

class EmbeddingService:
    _instance = None
    _model = None
    _reranker = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
            cls._instance.can_encode = HAS_ML
        return cls._instance

    def load_model(self):
        """Lazy load the embedding model."""
        if not HAS_ML:
            logger.warning("ML libraries (torch/sentence-transformers) not found. Semantic search disabled.")
            return

        if self._model is None:
            logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL_NAME}")
            try:
                self._model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                self.can_encode = False
                raise

    def load_reranker(self):
        """Lazy load the reranker model."""
        if not HAS_ML:
            return

        if self._reranker is None:
            logger.info(f"Loading reranker model: {settings.RERANKER_MODEL_NAME}")
            try:
                self._reranker = CrossEncoder(settings.RERANKER_MODEL_NAME, max_length=512)
            except Exception as e:
                logger.error(f"Failed to load reranker model: {e}")
                pass

    def encode(self, texts: Union[str, List[str]]) -> np.ndarray:
        if not self.can_encode:
            # Should not be called if can_encode is False, but let's be safe
            return np.zeros((1, 384)) if isinstance(texts, str) else np.zeros((len(texts), 384))
            
        self.load_model()
        if isinstance(texts, str):
            texts = [texts]
        
        embeddings = self._model.encode(texts, convert_to_numpy=True)
        return embeddings

    def rerank(self, query: str, candidates: List[str]) -> np.ndarray:
        self.load_reranker()
        if not self._reranker:
            return np.zeros(len(candidates)) # Fallback if reranker fails load
            
        pairs = [[query, c] for c in candidates]
        scores = self._reranker.predict(pairs)
        return scores
