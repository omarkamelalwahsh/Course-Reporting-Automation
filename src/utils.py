"""
Utility functions for the course recommender system.
"""

import json
import os
import re
from datetime import datetime
from typing import List, Dict, Any

import pandas as pd


# --------------------------
# Text / Query Utilities
# --------------------------

_ARABIC_RE = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]")


def is_arabic(text: str) -> bool:
    """
    Returns True if the text contains at least one Arabic script character.
    Used for gating / routing logic.
    """
    if not isinstance(text, str) or not text.strip():
        return False
    return bool(_ARABIC_RE.search(text))


def normalize_query(text: str) -> str:
    """
    Normalize a user query for robust matching.
    - Converts to lowercase
    - Removes extra whitespace
    - Removes some punctuation
    - Keeps Arabic letters and English letters/numbers
    """
    if not isinstance(text, str):
        return ""

    text = text.strip().lower()

    # Replace punctuation with space (keep Arabic & English & numbers)
    text = re.sub(r"[^\w\u0600-\u06FF]+", " ", text, flags=re.UNICODE)

    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


# --------------------------
# Recommendation Persistence
# --------------------------

def save_recommendations(
    user_query: str,
    filters: Dict[str, Any],
    recommendations: List[Dict[str, Any]],
    output_path: str = "outputs/recommendations.json",
) -> None:
    """
    Save recommendation results to JSON file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    result = {
        "timestamp": datetime.now().isoformat(),
        "user_query": user_query,
        "filters": filters,
        "recommended_courses": recommendations,
    }

    # Load existing data if file exists
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                if not isinstance(data, list):
                    data = [data]
            except json.JSONDecodeError:
                data = []
    else:
        data = []

    data.append(result)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# --------------------------
# Data Loading & Formatting
# --------------------------

def load_courses(csv_path: str) -> pd.DataFrame:
    """
    Load courses from CSV file.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Courses file not found: {csv_path}")

    df = pd.read_csv(csv_path)

    required_cols = [
        "course_id",
        "title",
        "category",
        "level",
        "duration_hours",
        "skills",
        "description",
    ]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    return df


def format_course_text(row: pd.Series) -> str:
    """
    Format course information into a single text for embedding.
    """
    return f"{row['title']}. Skills: {row['skills']}. {row['description']}"
