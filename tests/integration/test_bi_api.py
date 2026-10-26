"""Victory Crest One - Integration Tests for Business Intelligence & Document Export API
Verifies /api/v1/bi endpoints: dashboards, cross-property benchmarks, department contributions,
financial ratios, and PDF/Excel/CSV document artifact generation.
"""

from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_get_bi_dashboard(client):
    res = client.get("/api/v1/bi/dashboard")
    assert res.status_code == 200
    data = res.json()

    assert "telemetry" in data
    assert "monthly_trend" in data
    assert "properties_benchmark" in data
    assert "department_contributions" in data
    assert "financial_ratios" in data

    telemetry = data["telemetry"]
    assert Decimal(str(telemetry["total_revenue"])) > Decimal("10000000.00")
    assert Decimal(str(telemetry["gop"])) > Decimal("4000000.00")
    assert Decimal(str(telemetry["ebitda"])) > Decimal("3000000.00")
    assert Decimal(str(telemetry["blended_occupancy_percent"])) > Decimal("60.00")

    # 12 months trend
    assert len(data["monthly_trend"]) == 12

    # 3 properties
    assert len(data["properties_benchmark"]) == 3
    prop_codes = [p["property_code"] for p in data["properties_benchmark"]]
    assert "MDU-HERITAGE" in prop_codes
    assert "KOD-RESORT" in prop_codes
    assert "MAA-CORP" in prop_codes

    # 4 departments
    assert len(data["department_contributions"]) == 4


def test_get_bi_telemetry(client):
    res = client.get("/api/v1/bi/telemetry")
    assert res.status_code == 200
    data = res.json()

    assert "total_revenue" in data
    assert "gop" in data
    assert "ebitda" in data
    assert "net_income" in data
    assert "cash_balance" in data
    assert "blended_occupancy_percent" in data


def test_get_bi_ratios(client):
    res = client.get("/api/v1/bi/ratios")
    assert res.status_code == 200
    ratios = res.json()

    assert Decimal(str(ratios["gross_margin_percent"])) > Decimal("50.00")
    assert Decimal(str(ratios["gop_margin_percent"])) > Decimal("30.00")
    assert Decimal(str(ratios["operating_margin_percent"])) > Decimal("20.00")
    assert Decimal(str(ratios["current_ratio"])) > Decimal("1.50")


def test_get_bi_departments_and_properties(client):
    dept_res = client.get("/api/v1/bi/departments")
    assert dept_res.status_code == 200
    depts = dept_res.json()
    assert len(depts) >= 3
    assert any("Hospitality" in d["department"] for d in depts)

    props_res = client.get("/api/v1/bi/properties")
    assert props_res.status_code == 200
    props = props_res.json()
    assert len(props) >= 3


def test_generate_and_download_excel_report(client):
    payload = {
        "report_type": "FINANCIAL_PERFORMANCE",
        "period": "YEAR_TO_DATE",
        "format": "EXCEL",
        "notes": "Automated test spreadsheet compilation"
    }
    gen_res = client.post("/api/v1/bi/reports/generate", json=payload)
    assert gen_res.status_code == 200
    report_meta = gen_res.json()

    rep_id = report_meta["id"]
    assert report_meta["format"] == "EXCEL"

    # Download report artifact
    dl_res = client.get(f"/api/v1/bi/reports/download/{rep_id}")
    assert dl_res.status_code == 200
    assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in dl_res.headers.get("content-type", "")
    assert len(dl_res.content) > 1000  # Valid binary Excel payload


def test_generate_and_download_pdf_report(client):
    payload = {
        "report_type": "EXECUTIVE_SUMMARY",
        "period": "QUARTERLY",
        "format": "PDF",
        "notes": "Automated executive PDF compilation"
    }
    gen_res = client.post("/api/v1/bi/reports/generate", json=payload)
    assert gen_res.status_code == 200
    report_meta = gen_res.json()

    rep_id = report_meta["id"]
    assert report_meta["format"] == "PDF"

    # Download report artifact
    dl_res = client.get(f"/api/v1/bi/reports/download/{rep_id}")
    assert dl_res.status_code == 200
    assert "application/pdf" in dl_res.headers.get("content-type", "")
    assert dl_res.content.startswith(b"%PDF")  # Valid PDF header signature


def test_generate_and_download_csv_report(client):
    payload = {
        "report_type": "DEPARTMENTAL_P_AND_L",
        "period": "MONTHLY",
        "format": "CSV"
    }
    gen_res = client.post("/api/v1/bi/reports/generate", json=payload)
    assert gen_res.status_code == 200
    rep_id = gen_res.json()["id"]

    dl_res = client.get(f"/api/v1/bi/reports/download/{rep_id}")
    assert dl_res.status_code == 200
    assert "text/csv" in dl_res.headers.get("content-type", "")
    csv_text = dl_res.text
    assert "VICTORY CREST ONE" in csv_text
    assert "DEPARTMENTAL CONTRIBUTION" in csv_text
