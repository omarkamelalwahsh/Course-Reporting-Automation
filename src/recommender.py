import os
import json
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Union
try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:
    SentenceTransformer = None
    cosine_similarity = None

from src.utils import (
    load_courses, 
    format_course_text, 
    validate_and_clean_dataset,
    build_abbreviation_map,
    get_dataset_hash,
    expand_query
)

class CourseRecommender:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2', model: Any = None):
        """
        Initialize the Course Recommender system.
        
        Args:
            model_name: Name of the model to load if not provided.
            model: Optional pre-loaded SentenceTransformer model.
        """
        self.model_name = model_name
        self.model = model
        self.courses_df = None
        self.embeddings = None
        self.abbr_map = {}
        self.dataset_hash = None
        
        # Fallback data
        self.fallback_data = [
            {
                "course_id": 1,
                "title": "Python for Beginners",
                "category": "Programming",
                "level": "Beginner",
                "duration_hours": 10.5,
                "skills": "Python, Basic Syntax, Loops",
                "description": "Learn Python programming from scratch."
            },
            {
                "course_id": 2,
                "title": "Advanced Machine Learning",
                "category": "Data Science",
                "level": "Advanced",
                "duration_hours": 25.0,
                "skills": "Deep Learning, Neural Networks, TensorFlow, NLP",
                "description": "Master advanced ML concepts and frameworks including Natural Language Processing (NLP)."
            },
            {
                "course_id": 3,
                "title": "Web Development Bootcamp",
                "category": "Web Development",
                "level": "Intermediate",
                "duration_hours": 40.0,
                "skills": "HTML, CSS, JavaScript, React",
                "description": "Complete guide to modern web development."
            },
            {
                "course_id": 4,
                "title": "Data Analysis with Pandas",
                "category": "Data Science",
                "level": "Intermediate",
                "duration_hours": 12.0,
                "skills": "Pandas, NumPy, Data Cleaning",
                "description": "Analyze real-world data using Python libraries."
            },
            {
                "course_id": 5,
                "title": "Introduction to SQL",
                "category": "Database",
                "level": "Beginner",
                "duration_hours": 8.0,
                "skills": "SQL, Database Design, Querying",
                "description": "Learn to manage and query relational databases."
            }
        ]

    def _initialize_model(self):
        """Initialize the sentence transformer model if available."""
        if self.model is None and SentenceTransformer is not None:
            print(f"Loading model: {self.model_name}...")
            self.model = SentenceTransformer(self.model_name)
            print("Model loaded.")

    def load_courses(self, source: Union[str, pd.DataFrame]) -> None:
        """
        Load courses from CSV path or DataFrame with caching support.
        """
        try:
            # 1. Load and Clean Data
            if isinstance(source, pd.DataFrame):
                print("Loading courses from DataFrame...")
                self.courses_df = validate_and_clean_dataset(source)
            else:
                print(f"Loading courses from {source}...")
                if os.path.exists(source):
                    raw_df = pd.read_csv(source)
                    self.courses_df = validate_and_clean_dataset(raw_df)
                else:
                    raise FileNotFoundError(f"File not found: {source}")
            
            # 2. Compute Hash
            self.dataset_hash = get_dataset_hash(self.courses_df)
            print(f"Dataset Hash: {self.dataset_hash}")
            
            # 3. Check Cache
            cache_dir = "outputs"
            os.makedirs(cache_dir, exist_ok=True)
            
            emb_path = os.path.join(cache_dir, f"embeddings_{self.dataset_hash}.npy")
            map_path = os.path.join(cache_dir, f"abbr_map_{self.dataset_hash}.json")
            data_path = os.path.join(cache_dir, f"courses_{self.dataset_hash}.csv")
            
            if os.path.exists(emb_path) and os.path.exists(map_path):
                print("Found cached embeddings and map. Loading...")
                self.embeddings = np.load(emb_path)
                with open(map_path, 'r') as f:
                    self.abbr_map = json.load(f)
                # Ensure model is loaded for query encoding
                self._initialize_model()
            else:
                print("No cache found. Computing embeddings and map...")
                # Build Abbreviation Map
                self.abbr_map = build_abbreviation_map(self.courses_df)
                
                # Compute Embeddings
                self._compute_embeddings()
                
                # Save Cache
                if self.embeddings is not None:
                    np.save(emb_path, self.embeddings)
                    print(f"Saved embeddings to {emb_path}")
                
                with open(map_path, 'w') as f:
                    json.dump(self.abbr_map, f)
                    print(f"Saved abbreviation map to {map_path}")
                    
                self.courses_df.to_csv(data_path, index=False)
                print(f"Saved cleaned dataset to {data_path}")
                
        except Exception as e:
            print(f"Error loading courses: {e}. Using fallback data.")
            self.courses_df = validate_and_clean_dataset(pd.DataFrame(self.fallback_data))
            # Even for fallback, we need to init model and simple embeddings
            self.abbr_map = build_abbreviation_map(self.courses_df)
            self._compute_embeddings()

    def _compute_embeddings(self) -> None:
        """Compute embeddings for all courses."""
        if self.courses_df is None or self.courses_df.empty:
            print("No courses to embed.")
            return

        # Use format_course_text with the abbreviation map
        self.courses_df['combined_text'] = self.courses_df.apply(
            lambda row: format_course_text(row, self.abbr_map), axis=1
        )
        
        self._initialize_model()
        
        if self.model:
            print("Computing embeddings...")
            self.embeddings = self.model.encode(self.courses_df['combined_text'].tolist(), show_progress_bar=True)
            print("Embeddings computed.")
        else:
            print("Warning: SentenceTransformer not available. Embeddings not computed.")

    def recommend(
        self, 
        user_query: str, 
        top_k: int = 30, 
        pre_filters: Optional[Dict[str, Any]] = None,
        similarity_threshold: float = 0.25
    ) -> Dict[str, Any]:
        """
        Get course recommendations with pre-filtering, similarity threshold, and debug info.
        """
        if self.courses_df is None:
            # Try loading default if not loaded
            self.load_courses("data/courses.csv")

        debug_info = {
            "query": user_query,
            "expanded_query": user_query, # To show expansion
            "pre_filter_count": 0,
            "total_courses": len(self.courses_df) if self.courses_df is not None else 0,
            "top_raw_scores": [],
            "keyword_warning": None
        }

        if not user_query.strip():
            return {"results": [], "debug_info": debug_info}
            
        # --- 0. Expand Query ---
        expanded_query = expand_query(user_query, self.abbr_map)
        debug_info["expanded_query"] = expanded_query

        # --- 1. Apply Pre-Run Hard Filters ---
        filtered_df = self.courses_df.copy()
        
        if pre_filters:
            if 'level' in pre_filters and pre_filters['level'] != "Any":
                filtered_df = filtered_df[filtered_df['level'] == pre_filters['level']]
            
            if 'category' in pre_filters and pre_filters['category'] != "Any":
                filtered_df = filtered_df[filtered_df['category'] == pre_filters['category']]
                
            if 'max_duration' in pre_filters and 'duration_hours' in filtered_df.columns:
                 filtered_df = filtered_df[filtered_df['duration_hours'] <= pre_filters['max_duration']]

        debug_info["pre_filter_count"] = len(filtered_df)

        if filtered_df.empty:
            return {"results": [], "debug_info": debug_info}

        # --- Keyword Guardrail ---
        query_words = set(expanded_query.lower().split())
        stop_words = {'i', 'want', 'to', 'learn', 'course', 'advanced', 'beginner', 'intermediate', 'in', 'of', 'for', 'and', 'with', 'a', 'the'}
        keywords = [w for w in query_words if w not in stop_words and len(w) > 2]
        
        missing_keywords = []
        if keywords:
            # Check availability in the *filtered* dataset text
            all_text_blob = " ".join(filtered_df['combined_text'].str.lower().tolist())
            for kw in keywords:
                if kw not in all_text_blob:
                    missing_keywords.append(kw)
        
        if missing_keywords:
            debug_info["keyword_warning"] = f"No courses related to '{', '.join(missing_keywords)}' found in the filtered dataset."
            # We return empty if we are fairly strict, or we can proceed.
            # Given the user request for reliability, let's treat this as a soft fail/warning but return results if we can?
            # Actually, per prompt "stop safely" - returning empty list with warning is safe.
            return {"results": [], "debug_info": debug_info}


        # --- Semantic Search ---
        current_indices = filtered_df.index.tolist()
        results = []
        
        if self.model and self.embeddings is not None and len(self.embeddings) == len(self.courses_df):
            # 1. Compute Query Embedding (Freshly computed)
            query_embedding = self.model.encode([expanded_query])
            
            # 2. Slice Embeddings
            subset_embeddings = self.embeddings[current_indices]
            
            # 3. Cosine Similarity
            similarities = cosine_similarity(query_embedding, subset_embeddings)[0]
            
            # 4. Filter by Threshold
            valid_mask = similarities >= similarity_threshold
            
            if not np.any(valid_mask):
                top_debug_indices = np.argsort(similarities)[::-1][:5]
                debug_info["top_raw_scores"] = similarities[top_debug_indices].tolist()
                return {"results": [], "debug_info": debug_info}
            
            filtered_similarities = similarities[valid_mask]
            valid_subset_indices = np.where(valid_mask)[0]
            
            # Sort valid ones
            sorted_local_indices = valid_subset_indices[np.argsort(filtered_similarities)[::-1]]
            
            # Additional capping by top_k
            top_local_indices = sorted_local_indices[:top_k]
            
            final_subset_scores = []
            for local_idx in top_local_indices:
                final_subset_scores.append(similarities[local_idx])
            
            final_subset_scores = np.array(final_subset_scores)
            
            # DEBUG: Store top 5 raw scores
            debug_info["top_raw_scores"] = [float(s) for s in final_subset_scores[:5]]
            
            # Calculate Rank 0..10 based on these VALID scores
            min_score = np.min(final_subset_scores) if len(final_subset_scores) > 0 else 0.0
            max_score = np.max(final_subset_scores) if len(final_subset_scores) > 0 else 1.0
            
            for local_idx, score in zip(top_local_indices, final_subset_scores):
                course = filtered_df.iloc[local_idx].to_dict()
                course['similarity_score'] = float(score)
                
                # Integer Rank Calculation
                if max_score == min_score:
                    rank = 10 # If all same and valid, give 10
                else:
                    rank = round(((score - min_score) / (max_score - min_score)) * 10)
                
                course['rank'] = int(rank)
                results.append(course)
                
        else:
            # Fallback: Keyword matching
            print("Using keyword matching fallback.")
            query_lower = expanded_query.lower()
            
            def keyword_score(text):
                return sum(1 for word in query_lower.split() if word in str(text).lower())
            
            scores = filtered_df['combined_text'].apply(keyword_score)
            scores = scores[scores > 0]
            
            if scores.empty:
                return {"results": [], "debug_info": debug_info}

            top_indices = scores.nlargest(top_k).index 
            
            debug_info["top_raw_scores"] = scores.nlargest(5).tolist()

            subset_scores = scores[top_indices]
            min_score = subset_scores.min()
            max_score = subset_scores.max()
            
            for idx in top_indices:
                course = self.courses_df.loc[idx].to_dict()
                score = scores[idx]
                course['similarity_score'] = float(score)
                
                if max_score == min_score:
                    rank = 10
                else:
                    rank = round(((score - min_score) / (max_score - min_score)) * 10)
                
                course['rank'] = int(rank)
                results.append(course)

        return {"results": results, "debug_info": debug_info}
