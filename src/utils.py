"""
Utility functions for the course recommender system.
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Any
import pandas as pd


def save_recommendations(
    user_query: str,
    filters: Dict[str, Any],
    recommendations: List[Dict[str, Any]],
    output_path: str = "outputs/recommendations.json"
) -> None:
    """
    Save recommendation results to JSON file.
    
    Args:
        user_query: User's search query
        filters: Applied filters (level, duration, category)
        recommendations: List of recommended courses with scores
        output_path: Path to output JSON file
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    result = {
        "timestamp": datetime.now().isoformat(),
        "user_query": user_query,
        "filters": filters,
        "recommended_courses": recommendations
    }
    
    # Load existing data if file exists
    if os.path.exists(output_path):
        with open(output_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                if not isinstance(data, list):
                    data = [data]
            except json.JSONDecodeError:
                data = []
    else:
        data = []
    
    # Append new result
    data.append(result)
    
    # Save back to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_courses(csv_path: str) -> pd.DataFrame:
    """
    Load courses from CSV file.
    
    Args:
        csv_path: Path to courses CSV file
        
    Returns:
        DataFrame with course data
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Courses file not found: {csv_path}")
    
    df = pd.read_csv(csv_path)
    
    # Validate required columns
    required_cols = ['course_id', 'title', 'category', 'level', 'duration_hours', 'skills', 'description']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    return df


def format_course_text(row: pd.Series) -> str:
    """
    Format course information into a single text for embedding.
    
    Args:
        row: Course row from DataFrame
        
    Returns:
        Formatted text combining title, skills, and description
    """
    return f"{row['title']}. Skills: {row['skills']}. {row['description']}"
