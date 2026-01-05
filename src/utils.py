"""
Utility functions for the course recommender system.
"""
import json
import os
import re
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Tuple
import pandas as pd


def save_recommendations(
    user_query: str,
    filters: Dict[str, Any],
    recommendations: List[Dict[str, Any]],
    output_path: str = "outputs/recommendations.json"
) -> None:
    """
    Save recommendation results to JSON file.
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


def get_dataset_hash(df: pd.DataFrame) -> str:
    """
    Compute a stable hash of the dataframe content to identify dataset versions.
    """
    # Sort by columns and then index to ensure stability
    df_sorted = df.sort_index(axis=1).sort_index(axis=0)
    # Convert to string and hash
    content = pd.util.hash_pandas_object(df_sorted, index=True).values
    return hashlib.md5(content).hexdigest()


def validate_and_clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate and auto-fix the dataset schema for the Zedny dataset.
    Columns: course_id, title, category, level, duration_hours, skills, description, instructor, cover
    """
    df = df.copy()
    
    # 1. Normalize Column Names (if they differ from spec)
    col_map = {
        'id': 'course_id',
        'name': 'title',
        'course_name': 'title',
        'tags': 'skills',
        'desc': 'description'
    }
    df.rename(columns=lambda x: col_map.get(x.lower(), x), inplace=True)
    df.columns = [c.lower() for c in df.columns]

    # Required columns and their defaults
    # We handle course_id separately because it's a sequence
    if 'course_id' not in df.columns:
        df['course_id'] = list(range(1, len(df) + 1))
    else:
        df['course_id'] = df['course_id'].fillna(-1) # Placeholder or just leave as is if unique

    defaults = {
        'title': '',
        'category': 'General',
        'level': 'Beginner',
        'duration_hours': 0.0,
        'skills': '',
        'description': '',
        'instructor': 'Unknown',
        'cover': ''
    }
    
    for col, default in defaults.items():
        if col not in df.columns:
            df[col] = default
        else:
            df[col] = df[col].fillna(default)
            if col == 'category':
                df[col] = df[col].replace(['', 'nan'], 'General')

    # 2. Normalize 'level' strictly to Beginner / Intermediate / Advanced
    def normalize_level(val):
        val = str(val).lower()
        if any(x in val for x in ['beg', 'jun', 'intro', 'start']):
            return 'Beginner'
        if any(x in val for x in ['adv', 'exp', 'sen', 'deep', 'mast']):
            return 'Advanced'
        if any(x in val for x in ['inter', 'med', 'mid']):
            return 'Intermediate'
        return 'Intermediate' # Default for ambiguous cases

    df['level'] = df['level'].apply(normalize_level)

    # 3. Clean 'duration_hours'
    def extract_hours(val):
        if pd.isna(val) or val == '': 
            return 0.0
        if isinstance(val, (int, float)):
            return float(val)
        match = re.search(r"(\d+(\.\d+)?)", str(val))
        if match:
            return float(match.group(1))
        return 0.0

    df['duration_hours'] = df['duration_hours'].apply(extract_hours)

    # 4. Auto Skill Extraction if empty
    def extract_skills(row):
        skills = str(row['skills']).strip()
        if not skills or skills.lower() == 'nan':
            # Simple keyword extraction from title and description
            text = f"{row['title']} {row['description']}"
            tech_keywords = {
                'python', 'javascript', 'js', 'react', 'node', 'sql', 'html', 'css', 
                'java', 'c#', 'php', 'laravel', 'flutter', 'aws', 'azure', 'docker',
                'kubernetes', 'ml', 'ai', 'data science', 'marketing', 'sales',
                'excel', 'word', 'powerpoint', 'accounting', 'scrum', 'agile', 'wordpress'
            }
            extracted = set()
            words = re.findall(r'\b\w+\b', text.lower())
            for word in words:
                if word in tech_keywords:
                    extracted.add(word.capitalize())
            return "|".join(list(extracted)) if extracted else "General"
        return str(skills).replace(",", "|")

    df['skills'] = df.apply(extract_skills, axis=1)
    
    return df


def build_abbreviation_map(df: pd.DataFrame) -> Dict[str, str]:
    """
    Build abbreviation map automatically from dataset.
    Includes base tech mapping plus extracted patterns.
    """
    # Base mapping
    abbr_map = {
        'ml': 'machine learning',
        'dl': 'deep learning',
        'js': 'javascript',
        'nlp': 'natural language processing',
        'cv': 'computer vision',
        'ui/ux': 'user interface / user experience',
        'pm': 'project management',
        'bi': 'business intelligence'
    }
    
    # helper to clean
    def clean(text):
        return re.sub(r'[^a-zA-Z0-9\s/]', '', str(text).lower()).strip()

    # Regex for "Full Form (ABBR)" pattern
    pattern = re.compile(r'\((?P<abbr>[A-Z0-9]{2,6})\)')
    
    text_cols = ['title', 'description']
    for col in text_cols:
        if col not in df.columns: continue
        for text in df[col].dropna():
            for m in pattern.finditer(str(text)):
                abbr = m.group('abbr').lower()
                span_end = m.start()
                pre_text = str(text)[:span_end].strip()
                words = pre_text.split()
                if len(words) >= len(abbr):
                    potential_full = " ".join(words[-len(abbr):])
                    initials = "".join([w[0] for w in words[-len(abbr):] if w]).lower()
                    if initials == abbr:
                       abbr_map[abbr] = clean(potential_full)

    return abbr_map


def expand_query(query: str, abbr_map: Dict[str, str]) -> str:
    """
    Expand user query automatically using the mapping.
    Ensures both full words and abbreviations match (query contains both).
    """
    query_lower = query.lower()
    expanded = query_lower
    
    # We want "ML" -> "ML machine learning" so both match
    for abbr, full in abbr_map.items():
        # Match only whole words
        pattern = r'\b' + re.escape(abbr) + r'\b'
        if re.search(pattern, expanded):
            # Replace with "abbr full"
            expanded = re.sub(pattern, f"{abbr} {full}", expanded)
            
    return expanded


def format_course_text(row: pd.Series, abbr_map: Dict[str, str] = None) -> str:
    """
    Format course information into a single text for embedding.
    """
    text = f"{row['title']} {row['category']} {row['level']} {row['skills']} {row['description']}"
    return text.lower()


def load_courses(csv_path: str) -> pd.DataFrame:
    """
    Load data/courses.csv automatically.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Dataset missing at {csv_path}")
    
    df = pd.read_csv(csv_path)
    return validate_and_clean_dataset(df)
