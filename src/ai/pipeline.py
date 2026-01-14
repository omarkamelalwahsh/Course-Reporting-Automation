import time
from typing import Dict, Any, List
from src.logger import setup_logger
from src.schemas import RecommendRequest, RecommendResponse, Recommendation
from src.data_loader import DataLoader
from src.ai.embeddings import EmbeddingService
from src.ai.gating import check_gating
from src.ai.ranker import normalize_rank_1_10
from src.utils import normalize_query, is_arabic
from src.config import settings
from src.ai.gating import extract_strong_keywords_regex, STRICT_TECH_KEYWORDS

logger = setup_logger(__name__)

class CourseRecommenderPipeline:
    def __init__(self):
        self.data_loader = DataLoader()
        self.embedding_service = EmbeddingService()
        
        # Load data on init
        self.index, self.courses_df = self.data_loader.load_data()
        
        # Build Global Vocabulary for Strict Checking
        # We concat all titles, skills, and descriptions into a single text blob lowercased
        self.global_corpus_text = ""
        if self.courses_df is not None:
            self.global_corpus_text = " ".join(
                self.courses_df['title'].fillna('').astype(str).tolist() + 
                self.courses_df['skills'].fillna('').astype(str).tolist() + 
                self.courses_df['description'].fillna('').astype(str).tolist()
            ).lower()

    def recommend(self, request: RecommendRequest) -> RecommendResponse:
        start_time = time.time()
        
        if self.index is None or self.courses_df is None:
            return RecommendResponse(results=[], total_found=0, debug_info={"error": "Index missing"})

        # 1. Normalize Query
        original_query = request.query
        norm_query = normalize_query(original_query)
        is_ar = is_arabic(original_query)
        
        # --- GLOBAL DATA EXISTENCE CHECK (Strict) ---
        # 1. Extract Strict Keywords (e.g. ['python', 'c++']) using shared logic
        # We temporarily import extract function or replicate logic slightly for check
        
        strict_kws = extract_strong_keywords_regex(norm_query)
        # Filter only those that are in our STRICT list (like 'c++', 'java')
        # We don't want to block 'advanced' or 'learning' if they are not in global text (unlikely anyway)
        # But 'C++' is critical.
        
        critical_kws = [k for k in strict_kws if k.lower() in STRICT_TECH_KEYWORDS]
        
        for kw in critical_kws:
            # Check if this critical keyword exists ANYWHERE in our data
            # using simple heuristic: if kw not in global_corpus_text -> 0 results
            # We use strict boundaries check for short words like 'c', 'r', 'go' if needed, 
            # but for now simple ' in ' check is robust enough for 'c++', 'java', etc.
            
            # Special check for C++ to avoid partial match issues if needed, 
            # but 'c++' is unique enough.
            # Use regex search in global corpus for accuracy (avoid matching 'javascript' for 'java' check in corpus?)
            # Actually, global_corpus_text is huge. 'java' will match 'javascript'.
            # BUT: if 'java' is missing, it won't be there independently? 
            # If dataset has 'JavaScript Course', text has "... javascript ...".
            # 'java' in "javascript" is True.
            # So if user searches "Java" and we only have "JavaScript", this check PASSES (it thinks Java exists).
            # Then Gating logic later filters it out (because Gating is per-course).
            # So this is safe. 
            # The Danger is: User searches "C++". Dataset has NOTHING. 
            # 'c++' in text? False. -> RETURN 0. CORRECT.
            
            if kw.lower() not in self.global_corpus_text:
                logger.warning(f"Blocking query '{original_query}' because '{kw}' is not in database.")
                return RecommendResponse(
                    results=[], 
                    total_found=0, 
                    debug_info={
                        "blocked_reason": f"Topic '{kw}' not found in database.",
                        "time_taken": time.time() - start_time
                    }
                )

        # Determine strictness per query type
        tokens = norm_query.split()
        is_short_query = len(tokens) <= 2
        
        # Base Threshold Selection
        if is_ar:
            current_threshold = settings.SEMANTIC_THRESHOLD_ARABIC
        else:
            current_threshold = settings.SEMANTIC_THRESHOLD_GENERAL
            
        logger.info(f"Query: '{original_query}' | Norm: '{norm_query}' | Short: {is_short_query} | Threshold: {current_threshold}")
        
        logger.info(f"Query: '{original_query}' | Norm: '{norm_query}' | Short: {is_short_query} | Threshold: {current_threshold}")
        
        if self.embedding_service.can_encode:
            # 2. Semantic Search Path
            query_vector = self.embedding_service.encode(norm_query)
            D, I = self.index.search(query_vector, settings.TOP_K_Candidates)
            distances = D[0]
            indices = I[0]

            # 4. Filtering Strategy
            def filter_candidates(threshold_val):
                candidates = []
                for i, idx in enumerate(indices):
                    if idx == -1: continue 
                    
                    score = float(distances[i])
                    course = self.courses_df.iloc[idx].to_dict()
                    
                    if request.filters:
                        if request.filters.get('level') and request.filters['level'] != "Any":
                            if course.get('level') != request.filters['level']:
                                continue
                        if request.filters.get('category') and request.filters['category'] != "Any":
                            if course.get('category') != request.filters['category']:
                                continue

                    is_valid, matched_kws = check_gating(
                        course=course,
                        score=score,
                        normalized_query=norm_query,
                        original_query=original_query,
                        threshold=threshold_val,
                        is_short_query=is_short_query
                    )
                    
                    if is_valid:
                        candidates.append({
                            "title": course.get('title', ''),
                            "url": course.get('url', f"{settings.COURSE_BASE_URL}/{course.get('course_id')}"), 
                            "score": score,
                            "description": course.get('description', ''),
                            "skills": course.get('skills', ''),
                            "category": course.get('category', 'General'),
                            "level": course.get('level', 'All'),
                            "matched_keywords": matched_kws,
                            "why": [f"Keyword Matching" if score < 0.4 else "Semantic Match"]
                        })
                return candidates

            valid_candidates = filter_candidates(current_threshold)
            if len(valid_candidates) < 3 and not is_short_query:
                logger.info("Low results, attempting relaxed threshold...")
                valid_candidates = filter_candidates(settings.SEMANTIC_THRESHOLD_RELAXED)

        else:
            # Keyword Fallback Path (No Torch)
            logger.info("Performing keyword-based fallback search...")
            valid_candidates = []
            dummy_score = 1.0 
            
            for idx, row in self.courses_df.iterrows():
                course = row.to_dict()
                is_valid, matched_kws = check_gating(
                    course=course,
                    score=dummy_score,
                    normalized_query=norm_query,
                    original_query=original_query,
                    threshold=0.0, 
                    is_short_query=is_short_query
                )
                
                if is_valid and matched_kws:
                    valid_candidates.append({
                        "title": course.get('title', ''),
                        "url": course.get('url', f"{settings.COURSE_BASE_URL}/{course.get('course_id')}"), 
                        "score": 0.5, 
                        "description": course.get('description', ''),
                        "skills": course.get('skills', ''),
                        "category": course.get('category', 'General'),
                        "level": course.get('level', 'All'),
                        "matched_keywords": matched_kws,
                        "why": [f"Keyword Match: {', '.join(matched_kws[:2])}"]
                    })
                
                if len(valid_candidates) >= settings.TOP_K_Candidates:
                    break
        
        # Attempt 2: Fallback (Relaxed) if results are too low (< 3)
        if len(valid_candidates) < 3 and not is_short_query:
            # We don't relax for Short Queries (Python must mean Python)
            # We only relax for long distinct queries like "how to lead a team effectively"
            logger.info("Low results, attempting relaxed threshold...")
            valid_candidates = filter_candidates(SEMANTIC_THRESHOLD_RELAXED)

        # 5. Reranking (Optional)
        if request.enable_reranking and len(valid_candidates) > 1:
            top_slice = valid_candidates[:20]
            tail_slice = valid_candidates[20:]
            
            titles = [c['title'] for c in top_slice]
            rerank_scores = self.embedding_service.rerank(norm_query, titles)
            
            for i, r_score in enumerate(rerank_scores):
                top_slice[i]['score'] = float(r_score)
                top_slice[i]['why'].insert(0, f"Reranker: {r_score:.2f}")
                
            top_slice.sort(key=lambda x: x['score'], reverse=True)
            valid_candidates = top_slice + tail_slice

        # 6. Rank Normalization & Formatting
        final_results = valid_candidates[:request.top_k]
        final_results = normalize_rank_1_10(final_results)
        
        output_list = []
        for res in final_results:
            rec = Recommendation(
                title=res['title'],
                url=res['url'],
                rank=res['rank'],
                score=res['score'], 
                category=res.get('category', 'General'),
                level=res.get('level', 'Any'),
                matched_keywords=res['matched_keywords'],
                why=res['why'],
                debug_info={
                    "desc_snippet": res['description'][:150]
                }
            )
            output_list.append(rec)

        elapsed = time.time() - start_time
        return RecommendResponse(
            results=output_list,
            total_found=len(output_list),
            debug_info={
                "time_taken": elapsed,
                "original_query": original_query,
                "normalized_query": norm_query,
                "is_short_query": is_short_query,
                "threshold_used": current_threshold
            }
        )
