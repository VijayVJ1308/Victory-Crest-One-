"""Victory Crest One - Multi-Cloud Resiliency & Autonomous DR Schemas
Pydantic schemas for cross-cloud replica nodes, chaos failover drill triggers,
replication lag evaluations, and autonomous disaster recovery metrics.
"""

from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from shared.enums import (
    CloudProvider,
    ReplicationMode,
    NodeRole,
    NodeHealthStatus,
    FailoverDrillType,
    FailoverDrillStatus,
)


class CloudReplicaNodeBase(BaseModel):
    """Base schema attributes for cloud standby cluster node."""
    node_code: str = Field(..., description="Unique node identifier e.g. NODE-AWS-MUMBAI")
    name: str = Field(..., description="Descriptive node title")
    provider: CloudProvider = Field(..., description="Cloud provider (AWS, Azure, GCP, On-Premise)")
    region: str = Field(..., description="Data center region e.g. ap-south-1")
    role: NodeRole = Field(default=NodeRole.HOT_STANDBY, description="Cluster role")
    replication_mode: ReplicationMode = Field(default=ReplicationMode.SYNCHRONOUS)
    health_status: NodeHealthStatus = Field(default=NodeHealthStatus.HEALTHY)
    endpoint_url: Optional[str] = Field(default=None)
    property_id: Optional[str] = Field(default=None)


class CloudReplicaNodeCreate(CloudReplicaNodeBase):
    """Payload to register a new cloud replica node."""
    pass


class CloudReplicaNodeOut(CloudReplicaNodeBase):
    """Cloud replica node response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    replication_lag_seconds: Decimal
    sync_latency_ms: Decimal
    last_heartbeat_at: Optional[datetime] = None
    is_active: bool = True
    created_at: Optional[datetime] = None


class FailoverDrillBase(BaseModel):
    """Base schema attributes for chaos failover drill execution."""
    drill_code: str = Field(..., description="Unique drill code e.g. DRILL-2026-001")
    drill_type: FailoverDrillType = Field(..., description="Simulated failure scenario")
    target_primary_node: str = Field(..., description="Node experiencing failure")
    promoted_standby_node: str = Field(..., description="Standby node to promote to primary")
    simulated_failure: str = Field(..., description="Scenario description")


class FailoverDrillCreate(FailoverDrillBase):
    """Payload to record or configure a failover drill."""
    pass


class FailoverDrillOut(FailoverDrillBase):
    """Failover drill response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    status: FailoverDrillStatus
    actual_rto_seconds: Decimal
    actual_rpo_seconds: Decimal
    traffic_rerouted_percent: Decimal
    execution_log: Optional[str] = None
    executed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class FailoverTriggerRequest(BaseModel):
    """Trigger payload for autonomous or manual failover drill execution."""
    drill_type: FailoverDrillType = Field(default=FailoverDrillType.ZONE_OUTAGE)
    target_primary_node: Optional[str] = Field(default=None)
    promoted_standby_node: Optional[str] = Field(default=None)
    simulate_network_partition: bool = Field(default=True)


class FailoverTriggerResponse(BaseModel):
    """Result of failover drill initiation and switchover telemetry."""
    drill_id: str
    drill_code: str
    status: FailoverDrillStatus
    promoted_node: str
    demoted_node: str
    switchover_latency_seconds: Decimal
    data_loss_window_seconds: Decimal
    traffic_rerouted_percent: Decimal
    is_zero_rpo_achieved: bool
    summary: str


class ReplicationLagTestRequest(BaseModel):
    """Payload to evaluate cross-cloud replication lag and consensus stream."""
    node_code: str = Field(..., description="Target standby node code")
    simulated_bytes_behind: int = Field(default=0, ge=0)
    packet_loss_percent: float = Field(default=0.0, ge=0.0, le=100.0)


class ReplicationLagTestResponse(BaseModel):
    """Replication lag diagnostics response."""
    node_code: str
    replication_lag_seconds: Decimal
    lag_tier: str
    sync_latency_ms: Decimal
    is_zero_rpo: bool
    consensus_valid: bool


class DrResiliencyMetricsOut(BaseModel):
    """Consolidated enterprise multi-cloud DR telemetry."""
    resiliency_score: Decimal
    resiliency_tier: str
    cluster_availability_percent: Decimal
    total_nodes: int
    healthy_nodes: int
    active_primary_count: int
    hot_standby_count: int
    max_replication_lag_seconds: Decimal
    avg_replication_lag_seconds: Decimal
    total_drills: int
    succeeded_drills: int
    drill_success_rate_percent: Decimal
    avg_actual_rto_seconds: Decimal
    avg_actual_rpo_seconds: Decimal
    target_rto_seconds: Decimal
    target_rpo_seconds: Decimal
    rto_sla_met: bool
    rpo_sla_met: bool
    is_zero_rpo_compliant: bool
    providers_active: List[str]
