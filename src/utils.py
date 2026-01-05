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
    Validate and auto-fix the dataset schema.
    """
    df = df.copy()
    
    # 1. Normalize Column Names
    # Common mappings
    col_map = {
        'id': 'course_id',
        'name': 'title',
        'course_name': 'title',
        'duration': 'duration_hours',
        'hours': 'duration_hours',
        'skill': 'skills',
        'tags': 'skills',
        'desc': 'description',
        'content': 'description'
    }
    df.rename(columns=lambda x: col_map.get(x.lower(), x), inplace=True)
    df.columns = [c.lower() for c in df.columns]

    # Required columns
    required_cols = ['course_id', 'title', 'category', 'level', 'duration_hours', 'skills', 'description']
    
    # 2. Add Missing Columns with Defaults
    if 'course_id' not in df.columns:
        df['course_id'] = range(1, len(df) + 1)
    
    if 'category' not in df.columns:
        df['category'] = 'General'
        
    if 'level' not in df.columns:
        df['level'] = 'Beginner'
        
    if 'title' not in df.columns:
        df['title'] = ''
        
    if 'description' not in df.columns:
        df['description'] = ''
        
    if 'skills' not in df.columns:
        df['skills'] = ''

    if 'duration_hours' not in df.columns:
        df['duration_hours'] = 0.0

    # 3. Clean 'level' column
    def normalize_level(val):
        val = str(val).lower()
        if any(x in val for x in ['beg', 'jun', 'intro', 'start']):
            return 'Beginner'
        if any(x in val for x in ['adv', 'exp', 'sen', 'deep', 'mast']):
            return 'Advanced'
        return 'Intermediate' # Default for others like 'intermediate', 'med', etc.

    df['level'] = df['level'].fillna('Beginner').apply(normalize_level)

    # 4. Clean 'duration_hours'
    def extract_hours(val):
        if pd.isna(val): 
            return None
        # Extract number from string like "40 hours"
        match = re.search(r"(\d+(\.\d+)?)", str(val))
        if match:
            return float(match.group(1))
        return None

    df['duration_hours'] = df['duration_hours'].apply(extract_hours)
    # Fill missing duration with median
    median_dur = df['duration_hours'].median()
    if pd.isna(median_dur): median_dur = 10.0
    df['duration_hours'] = df['duration_hours'].fillna(median_dur)

    # 5. Clean 'skills'
    # Ensure string and separated by |
    def clean_skills(val):
        if pd.isna(val): return ""
        val = str(val)
        # Replace commas with |
        val = val.replace(",", "|")
        return val

    df['skills'] = df['skills'].apply(clean_skills)
    
    # 6. Fill missing text
    df['title'] = df['title'].fillna("")
    df['description'] = df['description'].fillna("")
    df['category'] = df['category'].fillna("General")
    
    # Ensure all required cols exist effectively now (we created them if missing)
    # Just select them to keep frame clean, + any others? No, lets keep others if user added them
    
    return df


def build_abbreviation_map(df: pd.DataFrame) -> Dict[str, str]:
    """
    Build abbreviation map automatically from dataset.
    Scans for:
    1. "Full Name (ABBR)" pattern
    2. "ABBR (Full Name)" pattern
    3. Acronyms in Skills (e.g. NLP -> "n l p")
    """
    abbr_map = {}
    
    # Helper to clean text
    def clean(text):
        return re.sub(r'[^a-zA-Z0-9\s]', '', str(text).lower())

    # 1. Regex for "Full Form (ABBR)" or "ABBR (Full Form)"
    # We look for something inside parens that is short (2-6 chars) and uppercase
    # And something outside that matches the letters
    
    # Simple Heuristic: Look for (XYZ) where XYZ is uppercase
    pattern = re.compile(r'\((?P<abbr>[A-Z0-9]{2,6})\)')
    
    text_cols = ['title', 'description']
    for col in text_cols:
        if col not in df.columns: continue
        
        for text in df[col].dropna():
            matches = pattern.finditer(str(text))
            for m in matches:
                abbr = m.group('abbr').lower()
                # Try to find full form before it? 
                # This is hard to do perfectly safely. 
                # For this task, we can just say: if we see (NLP), we map nlp -> "natural language processing" 
                # IF "Natural Language Processing" is immediately preceding.
                # However, the user asked to "Extract patterns".
                # A simpler robust way:
                # Capture the abbreviation. Map it to the whole string? No.
                
                # Let's try: "Natural Language Processing (NLP)"
                # We can grab X words before (NLP) where X is len(abbr).
                # Example: NLP = 3 chars. Check 3 words before.
                
                span_end = m.start()
                pre_text = str(text)[:span_end].strip()
                words = pre_text.split()
                if len(words) >= len(abbr):
                    potential_full = " ".join(words[-len(abbr):])
                    # Check if initials match
                    initials = "".join([w[0] for w in words[-len(abbr):]]).lower()
                    if initials == abbr:
                       abbr_map[abbr] = clean(potential_full) + " " + abbr

    # 2. Skill Acronyms
    # "Additionally, for any acronym detected in skills (2–8 uppercase/digits...)"
    # "map it to: 'abbr spaced-acronym'"
    if 'skills' in df.columns:
        for skills in df['skills'].dropna():
            # Split by | or ,
            tokens = re.split(r'[|;,]', str(skills))
            for token in tokens:
                token = token.strip()
                # Check if it is an acronym (all upper, 2-8 chars)
                if token.isupper() and 2 <= len(token) <= 8:
                    lowered = token.lower()
                    spaced = " ".join(list(lowered)) # nlp -> n l p
                    # If not already defined by Full Form extraction
                    if lowered not in abbr_map:
                         abbr_map[lowered] = f"{lowered} {spaced}"
    
    return abbr_map


def expand_query(query: str, abbr_map: Dict[str, str]) -> str:
    """
    Expand abbreviations in user query using the map.
    """
    tokens = query.lower().split()
    expanded_tokens = []
    
    for token in tokens:
        # Strip simple punctuation for matching
        clean_token = re.sub(r'\W+', '', token)
        if clean_token in abbr_map:
            expanded_tokens.append(abbr_map[clean_token])
        else:
            expanded_tokens.append(token)
            
    return " ".join(expanded_tokens)


def format_course_text(row: pd.Series, abbr_map: Dict[str, str] = None) -> str:
    """
    Format course information into a single text for embedding.
    Includes abbreviation expansion if map provided.
    """
    base_text = f"{row['title']}. Skills: {row['skills']}. {row['description']}"
    if abbr_map:
        return expand_query(base_text, abbr_map)
    return base_text


def load_courses(csv_path: str) -> pd.DataFrame:
    """
    Load and validate courses from CSV file.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Courses file not found: {csv_path}")
    
    df = pd.read_csv(csv_path)
    return validate_and_clean_dataset(df)
