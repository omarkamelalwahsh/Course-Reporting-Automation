import pytest
from unittest.mock import MagicMock, patch
from src.reports.catalog_weekly import build_catalog_weekly_report

@pytest.fixture
def mock_zedny_client():
    with patch("src.reports.catalog_weekly.ZednyClient") as mock:
        client_instance = mock.return_value
        
        # Mock categories
        client_instance.get_categories.return_value = [
            {"id": "1", "name": "Python", "product_count": 50},
            {"id": "2", "name": "Data Science", "product_count": 30},
            {"id": "3", "name": "Design", "product_count": 20},
            {"id": "4", "name": "Marketing", "product_count": 0},
        ]
        
        # Mock featured
        client_instance.get_featured.return_value = {
            "results": [
                {"title": "Intro to Python", "url": "/python-101", "category": "Python", "level": "Beginner"}
            ]
        }
        
        # Mock sliders
        client_instance.get_top_sliders.return_value = {
            "results": [
                {"name": "Master Data Science", "link": "/ds-master", "category_name": "Data Science", "difficulty": "Advanced"}
            ]
        }
        
        yield client_instance

def test_build_catalog_weekly_report_kpis(mock_zedny_client):
    report = build_catalog_weekly_report(top_n=2, bottom_n=2)
    
    assert report["kpis"]["total_categories"] == 4
    assert report["kpis"]["total_courses"] == 100
    
    # Check shares
    python_cat = next(c for c in report["categories"] if c["name"] == "Python")
    assert python_cat["share"] == 0.5
    
    design_cat = next(c for c in report["categories"] if c["name"] == "Design")
    assert design_cat["share"] == 0.2

def test_build_catalog_weekly_report_sorting(mock_zedny_client):
    report = build_catalog_weekly_report(top_n=2, bottom_n=2)
    
    assert len(report["top_categories"]) == 2
    assert report["top_categories"][0]["name"] == "Python"
    assert report["top_categories"][1]["name"] == "Data Science"
    
    assert len(report["low_coverage_categories"]) == 2
    assert report["low_coverage_categories"][0]["name"] == "Marketing"
    assert report["low_coverage_categories"][1]["name"] == "Design"

def test_build_catalog_weekly_report_parsing(mock_zedny_client):
    report = build_catalog_weekly_report()
    
    assert len(report["featured"]) == 1
    assert report["featured"][0]["title"] == "Intro to Python"
    
    assert len(report["top_sliders"]) == 1
    assert report["top_sliders"][0]["title"] == "Master Data Science"
    assert report["top_sliders"][0]["url"] == "/ds-master"

def test_build_catalog_weekly_report_markdown(mock_zedny_client):
    report = build_catalog_weekly_report()
    
    assert "# Weekly Catalog Intelligence Report" in report["markdown_summary"]
    assert "- **Total Categories:** 4" in report["markdown_summary"]
    assert "- **Total Courses:** 100" in report["markdown_summary"]
    assert "Python" in report["markdown_summary"]
    assert "Marketing" in report["markdown_summary"]
    assert "Intro to Python" in report["markdown_summary"]
