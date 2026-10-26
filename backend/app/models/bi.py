"""Victory Crest One - Business Intelligence & Executive Analytics Models
Persistent Report Snapshots, Multi-Dimensional Query Presets, and Analytical Metadata.
"""

from sqlalchemy import Column, String, Boolean, Text
from backend.app.models.base import Base, BaseModelMixin


class BiReportSnapshot(Base, BaseModelMixin):
    """Generated executive BI report snapshot and document artifact reference."""
    __tablename__ = "bi_report_snapshots"

    organization_id = Column(String(36), nullable=False, index=True)
    property_id = Column(String(36), nullable=True, index=True)

    report_type = Column(String(50), nullable=False, index=True)  # ReportType enum
    title = Column(String(255), nullable=False)
    period = Column(String(50), nullable=False)                   # MetricPeriod enum
    format = Column(String(20), nullable=False)                   # ReportFormat enum (JSON, CSV, EXCEL, PDF)

    file_path = Column(String(500), nullable=True)
    summary_metrics = Column(Text, nullable=True)                 # JSON string with top KPI figures
    generated_by_id = Column(String(36), nullable=True)
    generated_by_name = Column(String(255), nullable=True)


class BiSavedQuery(Base, BaseModelMixin):
    """Saved analytical query or customized KPI dashboard configuration."""
    __tablename__ = "bi_saved_queries"

    organization_id = Column(String(36), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    dimension = Column(String(50), nullable=False)                # AnalyticalDimension enum
    config_json = Column(Text, nullable=True)
    is_favorite = Column(Boolean, default=False, nullable=False)
