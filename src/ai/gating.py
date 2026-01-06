import re
from typing import List, Dict, Any
from src.utils import is_arabic
from src.config import SEMANTIC_THRESHOLD_ARABIC
from src.utils import normalize_query

def extract_strong_keywords_regex(query: str) -> List[str]:
    """Extract strong keywords for strict matching."""
    # This logic matches the original, but can be improved.
    # We use the normalized query for this.
    stopwords = {'course', 'learn', 'tutorial', 'basics', 'advanced', 'introduction', 'guide', 'complete', 'bootcamp'} 
    # Add more stopwords/logic as needed
    
    tokens = query.split()
    keywords = [t for t in tokens if t not in stopwords and len(t) > 2]
    return keywords

def check_gating(course: Dict[str, Any], query: str, score: float, normalized_query: str) -> bool:
    """
    Decides if a course is valid based on:
    1. Language check (Arabic -> Semantic Threshold)
    2. English -> Strict Keyword Gating
    """
    # 1. Arabic Check (on original query because normalization translates it)
    # Actually, we should check if the ORIGINAL query was Arabic.
    # But here we might receive the normalized one? 
    # The pipeline should pass both or we check the original. 
    # Let's assume 'query' is original user input.
    
    # ISSUE: normalize_query translates Arabic to English. 
    # So we need to detect Arabic BEFORE normalization, or pass a flag.
    # Let's check the original query for Arabic script.
    
    is_ar = is_arabic(query)
    
    if is_ar:
        # Semantic Threshold Fallback
        if score < SEMANTIC_THRESHOLD_ARABIC:
            return False
        return True
    
    # 2. Strict Keyword Gating (English/Translated)
    # Use normalized query to get English keywords
    keywords = extract_strong_keywords_regex(normalized_query)
    
    if not keywords:
        # If no strong keywords found (e.g. "learn course"), fallback to score or allow?
        # Strict gating says: if we can't find keywords, we might trust the score 
        # OR we block it. Let's block to be safe strictly.
        # But if query is "machine learning", we have keywords.
        return score >= 0.25 # Implicit weak threshold
        
    course_content = f"{course.get('title', '')} {course.get('skills', '')} {course.get('description', '')}".lower()
    
    found_any = False
    for kw in keywords:
        # Regex boundary match
        if re.search(r'\b' + re.escape(kw) + r'\b', course_content):
            found_any = True
            break
            
    return found_any
