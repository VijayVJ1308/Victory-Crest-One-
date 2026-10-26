"""Victory Crest One - Business Intelligence & Executive Analytics Endpoints
Multi-dimensional dashboards, cross-property benchmarks, department P&L,
financial ratios, and on-demand Excel, PDF, and CSV document generation.
"""

from typing import List, Optional
from fastapi import APIRouter, Query, Path, Body, HTTPException, Response, status
from backend.app.schemas.bi import (
    ExecutiveKpiTelemetry,
    PropertyPerformanceSummary,
    DepartmentContribution,
    FinancialRatiosOut,
    BiDashboardData,
    BiReportGenerateRequest,
    BiReportOut
)
from backend.app.services.bi_service import bi_service

router = APIRouter(prefix="/bi")


@router.get("/dashboard", response_model=BiDashboardData)
def get_bi_dashboard(
    organization_id: Optional[str] = Query(None, description="Filter by organization ID"),
    property_id: Optional[str] = Query(None, description="Filter by physical property ID")
):
    """Retrieve complete executive BI analytics dashboard payload."""
    return bi_service.get_dashboard_data(
        organization_id=organization_id,
        property_id=property_id
    )


@router.get("/telemetry", response_model=ExecutiveKpiTelemetry)
def get_bi_telemetry(
    organization_id: Optional[str] = Query(None, description="Filter by organization ID"),
    property_id: Optional[str] = Query(None, description="Filter by physical property ID")
):
    """Retrieve real-time consolidated executive financial and operational telemetry."""
    data = bi_service.get_dashboard_data(
        organization_id=organization_id,
        property_id=property_id
    )
    return data.telemetry


@router.get("/ratios", response_model=FinancialRatiosOut)
def get_bi_ratios(
    organization_id: Optional[str] = Query(None, description="Filter by organization ID"),
    property_id: Optional[str] = Query(None, description="Filter by physical property ID")
):
    """Retrieve financial health ratios (Gross Margin, GOP, Operating Margin, EBITDA, Net Margin, Current Ratio)."""
    data = bi_service.get_dashboard_data(
        organization_id=organization_id,
        property_id=property_id
    )
    return data.financial_ratios


@router.get("/departments", response_model=List[DepartmentContribution])
def get_bi_departments(
    organization_id: Optional[str] = Query(None, description="Filter by organization ID"),
    property_id: Optional[str] = Query(None, description="Filter by physical property ID")
):
    """Retrieve operating department revenue contribution, expense allocations, and net margins."""
    data = bi_service.get_dashboard_data(
        organization_id=organization_id,
        property_id=property_id
    )
    return data.department_contributions


@router.get("/properties", response_model=List[PropertyPerformanceSummary])
def get_bi_properties(
    organization_id: Optional[str] = Query(None, description="Filter by organization ID")
):
    """Retrieve comparative benchmarking matrix across all operating physical properties."""
    data = bi_service.get_dashboard_data(organization_id=organization_id)
    return data.properties_benchmark


@router.post("/reports/generate", response_model=BiReportOut)
def generate_bi_report(
    payload: BiReportGenerateRequest = Body(...),
    organization_id: Optional[str] = Query(None, description="Filter by organization ID")
):
    """Compile an on-demand executive analytical report (PDF, Excel, CSV, or JSON)."""
    report_meta, _, _, _ = bi_service.generate_report(payload, organization_id=organization_id)
    return report_meta


@router.get("/reports/history", response_model=List[BiReportOut])
def list_bi_reports(
    organization_id: Optional[str] = Query(None, description="Filter by organization ID")
):
    """List previously compiled report snapshots."""
    return bi_service.list_reports(organization_id=organization_id)


@router.get("/reports/download/{report_id}")
def download_bi_report(
    report_id: str = Path(..., description="Report snapshot ID")
):
    """Download binary artifact for a compiled report (Excel spreadsheet, PDF document, or CSV)."""
    res = bi_service.get_report_file(report_id)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report snapshot '{report_id}' not found."
        )

    content_bytes, media_type, filename = res
    return Response(
        content=content_bytes,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )
