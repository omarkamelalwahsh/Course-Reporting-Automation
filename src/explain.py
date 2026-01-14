"""
Explainability module for course recommendations.
Provides reasoning for why courses were recommended.
"""
from typing import List
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np


def generate_reasons(user_query: str, course_row: pd.Series, top_n: int = 3) -> List[str]:
    """
    Generate explanation for why a course was recommended.
    Uses TF-IDF to find matching keywords between query and course.
    
    Args:
        user_query: User's search query
        course_row: Course data row
        top_n: Number of top matching keywords to return
        
    Returns:
        List of reasons (matched skills/keywords)
    """
    # Combine course information
    course_text = f"{course_row['title']} {course_row['skills']} {course_row['description']}"
    
    # Extract skills as primary reasons
    skills = course_row['skills'].split('|')
    
    # Use TF-IDF to find keyword overlap
    try:
        vectorizer = TfidfVectorizer(stop_words='english', max_features=50)
        tfidf_matrix = vectorizer.fit_transform([user_query.lower(), course_text.lower()])
        
        # Get feature names
        feature_names = vectorizer.get_feature_names_out()
        
        # Get TF-IDF scores for query and course
        query_scores = tfidf_matrix[0].toarray()[0]
        course_scores = tfidf_matrix[1].toarray()[0]
        
        # Find common keywords (both have non-zero scores)
        common_keywords = []
        for idx, (q_score, c_score) in enumerate(zip(query_scores, course_scores)):
            if q_score > 0 and c_score > 0:
                common_keywords.append((feature_names[idx], q_score * c_score))
        
        # Sort by combined score
        common_keywords.sort(key=lambda x: x[1], reverse=True)
        
        # Extract top keywords
        matched_keywords = [kw[0] for kw in common_keywords[:top_n]]
        
    except Exception:
        # Fallback to simple word matching
        query_words = set(user_query.lower().split())
        course_words = set(course_text.lower().split())
        matched_keywords = list(query_words & course_words)[:top_n]
    
    # Build reasons
    reasons = []
    
    # Check for skill matches
    matched_skills = [skill for skill in skills if any(word in skill.lower() for word in user_query.lower().split())]
    if matched_skills:
        reasons.append(f"Matches skills: {', '.join(matched_skills[:2])}")
    
    # Add keyword matches
    if matched_keywords:
        reasons.append(f"Relevant keywords: {', '.join(matched_keywords)}")
    
    # Add level match if appropriate
    if 'beginner' in user_query.lower() and course_row['level'] == 'Beginner':
        reasons.append("Suitable for beginners")
    elif 'advanced' in user_query.lower() and course_row['level'] == 'Advanced':
        reasons.append("Advanced level content")
    
    # Add category match
    query_lower = user_query.lower()
    category_lower = course_row['category'].lower()
    if any(word in category_lower for word in query_lower.split()):
        reasons.append(f"Category: {course_row['category']}")
    
    # If no reasons found, provide generic one
    if not reasons:
        reasons.append(f"Related to: {course_row['category']}")
    
    return reasons[:3]  # Return top 3 reasons
