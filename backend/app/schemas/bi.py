"""Victory Crest One - Business Intelligence & Executive Analytics Pydantic Schemas
DTOs for Executive Telemetry, Cross-Property Benchmarks, Departmental P&L,
Financial Ratios, Forecasts, and Report Generation Snapshots.
"""

from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field
from shared.enums import ReportType, ReportFormat, MetricPeriod


class ExecutiveKpiTelemetry(BaseModel):
    """Real-time consolidated enterprise financial and operational metrics."""
    total_revenue: Decimal = Field(default=Decimal("0.00"), description="Total consolidated enterprise revenue")
    gop: Decimal = Field(default=Decimal("0.00"), description="Gross Operating Profit")
    gop_margin_percent: Decimal = Field(default=Decimal("0.00"), description="GOP Margin %")
    ebitda: Decimal = Field(default=Decimal("0.00"), description="Earnings Before Interest, Taxes, Depreciation & Amortization")
    ebitda_margin_percent: Decimal = Field(default=Decimal("0.00"), description="EBITDA Margin %")
    net_income: Decimal = Field(default=Decimal("0.00"), description="Bottom-line Net Profit")
    net_margin_percent: Decimal = Field(default=Decimal("0.00"), description="Net Profit Margin %")

    cash_balance: Decimal = Field(default=Decimal("0.00"), description="Liquid cash and bank balances (1010)")
    accounts_receivable: Decimal = Field(default=Decimal("0.00"), description="Outstanding customer receivables (1020)")
    accounts_payable: Decimal = Field(default=Decimal("0.00"), description="Outstanding vendor liabilities (2010)")

    blended_occupancy_percent: Decimal = Field(default=Decimal("0.00"), description="Weighted room occupancy %")
    average_adr: Decimal = Field(default=Decimal("0.00"), description="Portfolio Average Daily Rate")
    blended_revpar: Decimal = Field(default=Decimal("0.00"), description="Blended Revenue Per Available Room")

    active_projects: int = Field(default=0, description="Active WBS projects under delivery")
    pos_orders_today: int = Field(default=0, description="POS cashier register orders today")
    manufacturing_active_orders: int = Field(default=0, description="Active shop floor production orders")


class MonthlyTrendPoint(BaseModel):
    """Historical/projected monthly performance data point."""
    month: str = Field(..., description="Month identifier (e.g. 'Jan 2026')")
    revenue: Decimal = Field(default=Decimal("0.00"))
    expenses: Decimal = Field(default=Decimal("0.00"))
    net_profit: Decimal = Field(default=Decimal("0.00"))
    occupancy_percent: Decimal = Field(default=Decimal("0.00"))


class PropertyPerformanceSummary(BaseModel):
    """Comparative benchmarking metrics across physical operating properties."""
    property_id: str
    property_name: str
    property_code: str
    total_revenue: Decimal = Field(default=Decimal("0.00"))
    gop: Decimal = Field(default=Decimal("0.00"))
    gop_margin_percent: Decimal = Field(default=Decimal("0.00"))
    rooms_revenue: Decimal = Field(default=Decimal("0.00"))
    dining_revenue: Decimal = Field(default=Decimal("0.00"))
    retail_revenue: Decimal = Field(default=Decimal("0.00"))
    service_revenue: Decimal = Field(default=Decimal("0.00"))
    occupancy_percent: Decimal = Field(default=Decimal("0.00"))
    adr: Decimal = Field(default=Decimal("0.00"))
    revpar: Decimal = Field(default=Decimal("0.00"))
    staff_headcount: int = Field(default=0)


class DepartmentContribution(BaseModel):
    """Operational business division revenue and profitability contribution."""
    department: str
    revenue: Decimal = Field(default=Decimal("0.00"))
    expenses: Decimal = Field(default=Decimal("0.00"))
    net_profit: Decimal = Field(default=Decimal("0.00"))
    profit_margin_percent: Decimal = Field(default=Decimal("0.00"))
    revenue_share_percent: Decimal = Field(default=Decimal("0.00"))


class FinancialRatiosOut(BaseModel):
    """Comprehensive executive balance sheet and P&L financial ratios."""
    revenue: Decimal = Field(default=Decimal("0.00"))
    gross_profit: Decimal = Field(default=Decimal("0.00"))
    gross_margin_percent: Decimal = Field(default=Decimal("0.00"))
    gop: Decimal = Field(default=Decimal("0.00"))
    gop_margin_percent: Decimal = Field(default=Decimal("0.00"))
    ebit: Decimal = Field(default=Decimal("0.00"))
    operating_margin_percent: Decimal = Field(default=Decimal("0.00"))
    ebitda: Decimal = Field(default=Decimal("0.00"))
    ebitda_margin_percent: Decimal = Field(default=Decimal("0.00"))
    net_income: Decimal = Field(default=Decimal("0.00"))
    net_margin_percent: Decimal = Field(default=Decimal("0.00"))
    current_ratio: Decimal = Field(default=Decimal("0.00"))
    roa_percent: Decimal = Field(default=Decimal("0.00"))
    roe_percent: Decimal = Field(default=Decimal("0.00"))


class BiDashboardData(BaseModel):
    """Aggregated executive analytics payload for desktop and API consumers."""
    telemetry: ExecutiveKpiTelemetry
    monthly_trend: List[MonthlyTrendPoint]
    properties_benchmark: List[PropertyPerformanceSummary]
    department_contributions: List[DepartmentContribution]
    financial_ratios: FinancialRatiosOut
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class BiReportGenerateRequest(BaseModel):
    """Request payload to compile on-demand analytical reports."""
    report_type: ReportType = Field(default=ReportType.EXECUTIVE_SUMMARY)
    property_id: Optional[str] = Field(default=None, description="Optional property scope filter")
    period: MetricPeriod = Field(default=MetricPeriod.YEAR_TO_DATE)
    format: ReportFormat = Field(default=ReportFormat.PDF)
    notes: Optional[str] = Field(default=None)


class BiReportOut(BaseModel):
    """Metadata response for a generated report snapshot."""
    id: str
    organization_id: str
    property_id: Optional[str] = None
    report_type: str
    title: str
    period: str
    format: str
    file_path: Optional[str] = None
    download_url: Optional[str] = None
    summary_metrics: Optional[str] = None
    created_at: datetime
