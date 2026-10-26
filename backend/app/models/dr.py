"""Victory Crest One - Multi-Cloud Resiliency & Autonomous DR Models
Persistent cloud standby cluster nodes, cross-cloud replication streams, and chaos failover drill executions.
"""

from datetime import datetime
from sqlalchemy import Column, String, Boolean, Numeric, Text, DateTime
from backend.app.models.base import Base, BaseModelMixin


class CloudReplicaNode(Base, BaseModelMixin):
    """Multi-cloud distributed replica standby cluster node."""
    __tablename__ = "dr_cloud_replica_nodes"

    organization_id = Column(String(36), nullable=False, index=True)
    property_id = Column(String(36), nullable=True, index=True)

    node_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    provider = Column(String(50), nullable=False, index=True)  # CloudProvider
    region = Column(String(100), nullable=False)
    role = Column(String(30), default="HOT_STANDBY", nullable=False, index=True)  # NodeRole
    replication_mode = Column(String(30), default="SYNCHRONOUS", nullable=False)  # ReplicationMode
    health_status = Column(String(30), default="HEALTHY", nullable=False, index=True)  # NodeHealthStatus

    replication_lag_seconds = Column(Numeric(10, 3), default=0.000, nullable=False)
    sync_latency_ms = Column(Numeric(10, 2), default=12.50, nullable=False)
    endpoint_url = Column(String(255), nullable=True)
    last_heartbeat_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)


class FailoverDrillExecution(Base, BaseModelMixin):
    """Chaos engineering autonomous failover simulation and drill execution audit log."""
    __tablename__ = "dr_failover_drill_executions"

    organization_id = Column(String(36), nullable=False, index=True)

    drill_code = Column(String(50), unique=True, nullable=False, index=True)
    drill_type = Column(String(50), nullable=False, index=True)  # FailoverDrillType
    target_primary_node = Column(String(50), nullable=False)
    promoted_standby_node = Column(String(50), nullable=False)
    status = Column(String(30), default="SCHEDULED", nullable=False, index=True)  # FailoverDrillStatus

    simulated_failure = Column(Text, nullable=False)
    actual_rto_seconds = Column(Numeric(10, 2), default=0.00, nullable=False)
    actual_rpo_seconds = Column(Numeric(10, 2), default=0.00, nullable=False)
    traffic_rerouted_percent = Column(Numeric(5, 2), default=100.00, nullable=False)
    execution_log = Column(Text, nullable=True)
    executed_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
