"""
Simple smoke tests for the course recommender system.
Run without pytest: python tests/smoke_test.py
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.recommender import CourseRecommender
from src.utils import load_courses, create_fallback_dataset
import pandas as pd


def test_1_dataset_loading():
    """Test 1: Dataset loading with fallback works"""
    print("\n" + "="*60)
    print("TEST 1: Dataset Loading with Fallback")
    print("="*60)
    
    try:
        df = load_courses("data/courses.csv")
        
        assert df is not None, "Dataset is None"
        assert len(df) > 0, "Dataset is empty"
        assert "course_id" in df.columns, "Missing course_id column"
        assert "title" in df.columns, "Missing title column"
        
        print(f"PASSED: Loaded {len(df)} courses")
        print(f"   Columns: {list(df.columns)}")
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False


def test_2_normal_recommendation():
    """Test 2: Normal query returns results"""
    print("\n" + "="*60)
    print("TEST 2: Normal Recommendation Query")
    print("="*60)
    
    try:
        recommender = CourseRecommender()
        recommender.load_courses("data/courses.csv")
        
        results = recommender.recommend(
            user_query="I want to learn machine learning",
            level=None,
            max_duration=None,
            category=None,
            top_k=5
        )
        
        assert results is not None, "Results is None"
        assert len(results) > 0, "No results returned"
        assert "title" in results[0], "Missing title in result"
        assert "similarity_score" in results[0], "Missing similarity_score"
        
        print(f"PASSED: Got {len(results)} recommendations")
        print(f"   Top result: {results[0]['title']}")
        print(f"   Similarity: {results[0]['similarity_score']:.3f}")
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False


def test_3_empty_query():
    """Test 3: Empty query does not crash and returns empty list"""
    print("\n" + "="*60)
    print("TEST 3: Empty Query Handling")
    print("="*60)
    
    try:
        recommender = CourseRecommender()
        recommender.load_courses("data/courses.csv")
        
        results = recommender.recommend(
            user_query="",
            level=None,
            max_duration=None,
            category=None,
            top_k=5
        )
        
        assert results is not None, "Results should not be None"
        assert len(results) == 0, "Empty query should return empty list"
        
        print("PASSED: Empty query handled correctly")
        print("   Returned empty list without crash")
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False


def test_4_strict_filters():
    """Test 4: Strict filters return empty list without crash"""
    print("\n" + "="*60)
    print("TEST 4: Strict Filters Handling")
    print("="*60)
    
    try:
        recommender = CourseRecommender()
        recommender.load_courses("data/courses.csv")
        
        results = recommender.recommend(
            user_query="machine learning",
            level="Advanced",
            max_duration=10,
            category="NonExistentCategory",
            top_k=5
        )
        
        assert results is not None, "Results should not be None"
        
        print(f"PASSED: Strict filters handled correctly")
        print(f"   Returned {len(results)} results without crash")
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False


def run_all_tests():
    """Run all smoke tests"""
    print("\n" + "="*60)
    print("ZEDNY COURSE RECOMMENDER - SMOKE TESTS")
    print("="*60)
    
    tests = [
        test_1_dataset_loading,
        test_2_normal_recommendation,
        test_3_empty_query,
        test_4_strict_filters
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\nTest crashed: {e}")
            results.append(False)
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\nALL TESTS PASSED!")
        return 0
    else:
        print("\nSOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
