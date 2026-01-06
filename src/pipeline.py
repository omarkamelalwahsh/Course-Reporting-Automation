import time
from typing import Dict, Any, List
from src.logger import setup_logger
from src.schemas import RecommendRequest, RecommendResponse, Recommendation
from src.data_loader import DataLoader
from src.ai.embeddings import EmbeddingService
from src.ai.gating import check_gating
from src.ai.ranker import normalize_rank_1_10
from src.utils import normalize_query
from src.config import TOP_K_Candidates

logger = setup_logger(__name__)

class CourseRecommenderPipeline:
    def __init__(self):
        self.data_loader = DataLoader()
        self.embedding_service = EmbeddingService()
        
        # Load data on init (lazy or eager - eager here for simplicity)
        self.index, self.courses_df = self.data_loader.load_data()

    def recommend(self, request: RecommendRequest) -> RecommendResponse:
        start_time = time.time()
        
        if self.index is None or self.courses_df is None:
            logger.error("System not ready: Index or Data missing.")
            return RecommendResponse(results=[], total_found=0, debug_info={"error": "Index missing"})

        # 1. Normalize Query
        original_query = request.query
        norm_query = normalize_query(original_query)
        logger.info(f"Processing query: '{original_query}' -> '{norm_query}'")

        # 2. Embed Query
        query_vector = self.embedding_service.encode(norm_query)

        # 3. FAISS Search
        # Search TOP_K_Candidates (e.g. 100) to have enough buffer for filtering
        D, I = self.index.search(query_vector, TOP_K_Candidates)
        
        distances = D[0]
        indices = I[0]

        valid_candidates = []
        
        # 4. Filtering & Gating Loop
        for i, idx in enumerate(indices):
            if idx == -1: continue # FAISS padding
            
            score = float(distances[i])
            course = self.courses_df.iloc[idx].to_dict()
            
            # Strict Gating
            if not check_gating(course, original_query, score, norm_query):
                continue
                
            # Pre-filters (Category/Level)
            if request.filters:
                if request.filters.get('level') and request.filters['level'] != "Any":
                    if course.get('level') != request.filters['level']:
                        continue
                if request.filters.get('category') and request.filters['category'] != "Any":
                    if course.get('category') != request.filters['category']:
                        continue

            # Add to candidates
            title = course.get('title', '')
            if not isinstance(title, str): title = ""
            
            desc = course.get('description', '')
            if not isinstance(desc, str): desc = ""
            
            skills = course.get('skills', '')
            if not isinstance(skills, str): skills = ""
            
            valid_candidates.append({
                "title": title,
                "url": course.get('url', f"https://zedny.com/course/{course.get('course_id')}"), 
                "score": score,
                "description": desc,
                "skills": skills
            })

        # 5. Reranking (Optional)
        if request.enable_reranking and len(valid_candidates) > 1:
            # Rerank top 20
            top_slice = valid_candidates[:20]
            tail_slice = valid_candidates[20:]
            
            titles = [c['title'] for c in top_slice]
            rerank_scores = self.embedding_service.rerank(norm_query, titles)
            
            for i, r_score in enumerate(rerank_scores):
                top_slice[i]['score'] = float(r_score) # Update score with reranker score
                top_slice[i]['reranked'] = True
                
            # Sort by new score
            top_slice.sort(key=lambda x: x['score'], reverse=True)
            valid_candidates = top_slice + tail_slice

        # 6. Rank Normalization (1-10)
        # Limit to requested top_k first? Or rank all then cut?
        # Rank top_k
        final_results = valid_candidates[:request.top_k]
        final_results = normalize_rank_1_10(final_results)
        
        # Convert to Pydantic Models
        output_list = []
        for res in final_results:
            rec = Recommendation(
                title=res['title'],
                url=res['url'],
                rank=res['rank'],
                score=res['score'], 
                debug_info={
                    "desc_snippet": res['description'][:100],
                    "full_description": res['description'],
                    "skills": res.get('skills', '')
                }
            )
            output_list.append(rec)

        elapsed = time.time() - start_time
        logger.info(f"Recommendation finished in {elapsed:.4f}s. Found {len(output_list)} results.")
        
        return RecommendResponse(
            results=output_list,
            total_found=len(output_list),
            debug_info={
                "time_taken": elapsed,
                "original_query": original_query,
                "normalized_query": norm_query
            }
        )
