import re
from typing import List, Dict, Any, Tuple
from src.utils import is_arabic
from src.config import (
    SEMANTIC_THRESHOLD_ARABIC, 
    SEMANTIC_THRESHOLD_GENERAL, 
    SEMANTIC_THRESHOLD_RELAXED
)

def extract_strong_keywords_regex(query: str, is_short: bool = False) -> List[str]:
    """
    Extract strong keywords.
    If is_short=True (<=2 tokens), we trust tokens much more.
    """
    stopwords = {
        'course', 'learn', 'tutorial', 'basics', 'advanced', 'introduction', 
        'guide', 'complete', 'bootcamp', 'masterclass', 'fundamentals',
        'beginner', 'intermediate', 'expert'
    }
    
    tokens = query.split()
    # Keep tokens if they are NOT stopwords
    # For short queries, even 2-char tokens like "C#" or "GO" or "OS" might be relevant, 
    # but let's stick to len>1 to avoid 'a', 'i'.
    keywords = [t for t in tokens if t not in stopwords and len(t) >= 2]
    
    return keywords

def check_gating(
    course: Dict[str, Any], 
    score: float, 
    normalized_query: str,
    original_query: str,
    threshold: float = SEMANTIC_THRESHOLD_GENERAL,
    is_short_query: bool = False
) -> Tuple[bool, List[str]]:
    """
    Decides if a course is valid.
    Returns: (is_valid, list_of_matched_keywords)
    """
    
    # 1. Base Score Check
    if score < threshold:
        return False, []

    # 2. Extract Keywords
    keywords = extract_strong_keywords_regex(normalized_query, is_short_query)
    
    # If no keywords found (abstract query), we rely purely on score (which passed step 1)
    if not keywords:
        return True, [] 

    # 3. Keyword Matching
    title = str(course.get('title', '')).lower()
    skills = str(course.get('skills', '')).lower()
    desc = str(course.get('description', '')).lower()
    
    if title == 'nan': title = ''
    if skills == 'nan': skills = ''
    if desc == 'nan': desc = ''
    
    # Optimization: Check title first (fastest & most relevant)
    matched = []
    
    for kw in keywords:
        # Regex for word boundary
        pattern = r'\b' + re.escape(kw) + r'\b'
        
        # Check Title & Skills first
        if re.search(pattern, title) or re.search(pattern, skills):
            matched.append(kw)
            continue # Found this kw, move to next
            
        # Check Description last
        if re.search(pattern, desc):
            matched.append(kw)
    
    # 4. Gating Logic
    if is_short_query:
        # Strict: Must match at least one keyword for short queries
        # e.g. "Python" -> must find "python"
        if len(matched) > 0:
            return True, matched
        else:
            return False, []
    else:
        # Long query: "How to build a website with Python" -> "website", "python"
        # If we match 0 keywords but score is high, it might be semantic match.
        # But user requested "Strict Relevance Gating".
        # Let's say: if we have keywords, we expect SOME match.
        if len(matched) > 0:
            return True, matched
            
        # If score is VERY high, allow it without keyword match?
        # Let's stick to strict: if keywords exist, one must match.
        # Unless score is super high (e.g. > 0.6)
        if score > 0.60:
            return True, []
            
        return False, []
