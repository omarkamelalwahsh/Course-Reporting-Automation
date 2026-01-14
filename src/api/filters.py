from typing import List, Dict, Any, Optional

ROLE_FILTERS = {
    "Data Analyst": {
        "allowed_categories": ["Data", "Analytics", "Business", "SQL", "Python", "Excel", "Power BI", "Visualization"],
        "exclude_keywords": ["php", "unity", "game", "laravel", "wordpress", "frontend", "react", "nodejs"]
    },
    "ML Engineer": {
        "allowed_categories": ["Machine Learning", "Deep Learning", "AI", "Python", "Data", "MLOps", "NLP", "Computer Vision"],
        "exclude_keywords": ["unity", "game", "php", "wordpress"]
    },
    "Software Engineer": {
        "allowed_categories": ["Programming", "Backend", "Algorithms", "Databases", "System Design", "DevOps"],
        "exclude_keywords": ["unity", "game design"]
    }
}

def normalize_text(s: str) -> str:
    """Normalize text for consistent matching."""
    return s.strip().lower()

def apply_filters(
    results: List[Dict[str, Any]], 
    allowed_categories: Optional[List[str]] = None, 
    exclude_keywords: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Apply inclusive and exclusive filters to a list of results.
    
    Rules:
    - Exclude if any exclude_keyword exists in title or category (case-insensitive).
    - If allowed_categories provided: allow only if category contains at least one 
      allowed category substring (case-insensitive).
    """
    if not results:
        return []

    # Prepare normalized filter lists
    norm_allowed = [normalize_text(c) for c in allowed_categories] if allowed_categories else []
    norm_exclude = [normalize_text(k) for k in exclude_keywords] if exclude_keywords else []

    filtered = []
    
    for item in results:
        title = normalize_text(item.get("title", ""))
        category = normalize_text(item.get("category", ""))
        
        # 1. Check Exclusions
        is_excluded = False
        for ex in norm_exclude:
            if ex in title or ex in category:
                is_excluded = True
                break
        
        if is_excluded:
            continue
            
        # 2. Check Allowed Categories (if any)
        if norm_allowed:
            is_allowed = False
            for al in norm_allowed:
                if al in category:
                    is_allowed = True
                    break
            
            if not is_allowed:
                continue
                
        # 3. If passed both, keep
        filtered.append(item)
        
    return filtered
