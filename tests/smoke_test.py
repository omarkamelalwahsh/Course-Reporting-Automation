import requests
import sys
import time

BASE_URL = "http://localhost:8001"

def test_health():
    print("Testing /health...")
    resp = requests.get(f"{BASE_URL}/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    print("✅ Health check passed")

def test_catalog_weekly():
    print("Testing /reports/catalog-weekly...")
    resp = requests.get(f"{BASE_URL}/reports/catalog-weekly")
    assert resp.status_code == 200
    data = resp.json()
    assert "kpis" in data
    assert data["kpis"]["total_courses"] > 0
    print(f"✅ Catalog report passed ({data['kpis']['total_courses']} courses)")

def test_dashboard_png():
    print("Testing /reports/catalog-weekly/dashboard.png...")
    resp = requests.get(f"{BASE_URL}/reports/catalog-weekly/dashboard.png")
    assert resp.status_code == 200
    assert resp.headers["Content-Type"] == "image/png"
    assert len(resp.content) > 1000 # Should be at least 1KB
    print(f"✅ Dashboard PNG passed ({len(resp.content)} bytes)")

def test_report_html():
    print("Testing /reports/catalog-weekly/html...")
    resp = requests.get(f"{BASE_URL}/reports/catalog-weekly/html")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["Content-Type"]
    assert "Weekly Catalogue Intelligence Report" in resp.text
    print("✅ HTML Report passed")

def test_report_pdf():
    print("Testing /reports/catalog-weekly/pdf...")
    resp = requests.get(f"{BASE_URL}/reports/catalog-weekly/pdf")
    assert resp.status_code == 200
    assert resp.headers["Content-Type"] == "application/pdf"
    assert resp.content.startswith(b"%PDF-")
    print(f"✅ PDF Report passed ({len(resp.content)} bytes)")

def run_tests():
    print("--- STARTING SMOKE TESTS ---")
    try:
        test_health()
        test_catalog_weekly()
        test_dashboard_png()
        test_report_html()
        test_report_pdf()
        print("\n🏆 ALL TESTS PASSED!")
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # Wait a bit if running immediately after docker up
    if len(sys.argv) > 1 and sys.argv[1] == "--wait":
        print("Waiting 10s for service to settle...")
        time.sleep(10)
    run_tests()
