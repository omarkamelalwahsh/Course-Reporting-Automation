import pytest
from src.api.filters import apply_filters, normalize_text

def test_normalize_text():
    assert normalize_text("  Python  ") == "python"
    assert normalize_text("DATA ANALYST") == "data analyst"

def test_apply_filters_exclude():
    results = [
        {"title": "Python for Data Science", "category": "Data"},
        {"title": "PHP Basics", "category": "Web"},
        {"title": "Laravel Course", "category": "PHP"},
        {"title": "Advanced SQL", "category": "Databases"}
    ]
    
    exclude = ["php", "laravel"]
    filtered = apply_filters(results, exclude_keywords=exclude)
    
    assert len(filtered) == 2
    assert "PHP" not in filtered[0]["title"]
    assert "php" not in filtered[0]["category"].lower()

def test_apply_filters_allowed():
    results = [
        {"title": "Python for Data Science", "category": "Data Science"},
        {"title": "Unity Game Dev", "category": "Game"},
        {"title": "Business Intelligence", "category": "Analytics"},
    ]
    
    allowed = ["Data", "Analytics"]
    filtered = apply_filters(results, allowed_categories=allowed)
    
    assert len(filtered) == 2
    titles = [i["title"] for i in filtered]
    assert "Unity Game Dev" not in titles

def test_apply_filters_both():
    results = [
        {"title": "Python Programming", "category": "Programming"},
        {"title": "SQL for Analysts", "category": "Data"},
        {"title": "PHP for Dummies", "category": "Programming"},
        {"title": "React Frontend", "category": "Web Dev"},
    ]
    
    allowed = ["Programming", "Data"]
    exclude = ["php", "react"]
    
    filtered = apply_filters(results, allowed, exclude)
    
    assert len(filtered) == 2
    titles = [i["title"] for i in filtered]
    assert "Python Programming" in titles
    assert "SQL for Analysts" in titles
    assert "PHP for Dummies" not in titles

def test_apply_filters_empty():
    assert apply_filters([], ["cat"], ["word"]) == []
    results = [{"title": "Test", "category": "Test"}]
    assert apply_filters(results) == results
