import pytest
import pandas as pd
import os
from src.recommender import CourseRecommender
from src.utils import validate_and_clean_dataset

def test_dataset_loading():
    rec = CourseRecommender()
    rec.load_courses("data/courses.csv")
    assert rec.courses_df is not None
    assert not rec.courses_df.empty
    # Check if real columns exist after validation
    expected_cols = {'course_id', 'title', 'category', 'level', 'duration_hours', 'skills', 'description', 'instructor', 'cover'}
    assert expected_cols.issubset(set(rec.courses_df.columns))

def test_recommendation_basic():
    rec = CourseRecommender()
    rec.load_courses("data/courses.csv")
    response = rec.recommend("python", top_k=5)
    assert "results" in response
    assert isinstance(response["results"], list)
    assert len(response["results"]) <= 5

def test_rank_and_score():
    rec = CourseRecommender()
    rec.load_courses("data/courses.csv")
    response = rec.recommend("data science", top_k=5)
    results = response["results"]
    if results:
        for r in results:
            assert "rank" in r
            assert isinstance(r["rank"], int)
            assert 0 <= r["rank"] <= 10
            assert "similarity_score" in r

def test_pre_filters():
    rec = CourseRecommender()
    rec.load_courses("data/courses.csv")
    
    # Test Level Filter
    pre_filters = {"level": "Advanced"}
    response = rec.recommend("machine learning", pre_filters=pre_filters)
    for r in response["results"]:
        assert r["level"] == "Advanced"

def test_abbreviation_expansion():
    rec = CourseRecommender()
    rec.load_courses("data/courses.csv")
    
    # Query with JS
    resp_js = rec.recommend("js", top_k=10)
    # Query with JavaScript
    resp_full = rec.recommend("javascript", top_k=10)
    
    # Check if there is overlap (abbreviation works)
    titles_js = {r['title'] for r in resp_js['results']}
    titles_full = {r['title'] for r in resp_full['results']}
    
    overlap = titles_js.intersection(titles_full)
    assert len(overlap) > 0

def test_keyword_guardrail():
    rec = CourseRecommender()
    rec.load_courses("data/courses.csv")
    
    # Query with impossible keyword
    response = rec.recommend("qlzrkj123", top_k=5)
    assert len(response["results"]) == 0
    assert "keyword_warning" in response["debug_info"]
    assert "no courses about" in response["debug_info"]["keyword_warning"].lower()
