"""Victory Crest One - Multi-Cloud Resiliency & Autonomous DR REST API Endpoints
Distributed standby cluster node topology, automated chaos failover drills,
zero-RPO replication monitoring, and recovery time telemetry.
"""

from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException, status

from backend.app.schemas.dr import (
    CloudReplicaNodeCreate,
    CloudReplicaNodeOut,
    FailoverDrillOut,
    FailoverTriggerRequest,
    FailoverTriggerResponse,
    ReplicationLagTestRequest,
    ReplicationLagTestResponse,
    DrResiliencyMetricsOut,
)
from shared.enums import (
    CloudProvider,
    NodeRole,
    NodeHealthStatus,
    FailoverDrillType,
    FailoverDrillStatus,
)
from backend.app.services.dr_service import dr_service

router = APIRouter()


@router.get("/nodes", response_model=List[CloudReplicaNodeOut])
def list_replica_nodes(
    property_id: Optional[str] = Query(None, description="Filter nodes by property"),
    provider: Optional[CloudProvider] = Query(None, description="Filter by cloud provider"),
    role: Optional[NodeRole] = Query(None, description="Filter by node role"),
    status: Optional[NodeHealthStatus] = Query(None, description="Filter by health status")
):
    """Retrieve all distributed multi-cloud replica nodes."""
    return dr_service.get_nodes(property_id=property_id, provider=provider, role=role, status_filter=status)


@router.post("/nodes", response_model=CloudReplicaNodeOut, status_code=status.HTTP_201_CREATED)
def register_replica_node(payload: CloudReplicaNodeCreate):
    """Register a new standby cluster node across AWS, Azure, GCP, or On-Premise."""
    return dr_service.create_node(payload)


@router.post("/nodes/{node_id}/promote", response_model=CloudReplicaNodeOut)
def promote_node_to_primary(node_id: str):
    """Promote an active standby node to primary consensus leader."""
    return dr_service.promote_node(node_id)


@router.get("/drills", response_model=List[FailoverDrillOut])
def list_failover_drills(
    status: Optional[FailoverDrillStatus] = Query(None, description="Filter by drill status"),
    drill_type: Optional[FailoverDrillType] = Query(None, description="Filter by drill scenario")
):
    """Retrieve historical and scheduled chaos engineering failover drills."""
    return dr_service.get_drills(status_filter=status, drill_type=drill_type)


@router.post("/drills/trigger", response_model=FailoverTriggerResponse)
def trigger_failover_drill(payload: FailoverTriggerRequest):
    """Initiate an automated cross-cloud failover drill and calculate live RTO/RPO."""
    return dr_service.trigger_failover_drill(payload)


@router.post("/replication/test", response_model=ReplicationLagTestResponse)
def test_replication_lag(request: ReplicationLagTestRequest):
    """Simulate network partition or byte lag to evaluate zero-RPO consensus."""
    return dr_service.test_replication_lag(request)


@router.get("/metrics", response_model=DrResiliencyMetricsOut)
def get_dr_resiliency_metrics(
    property_id: Optional[str] = Query(None, description="Filter metrics by property")
):
    """Retrieve multi-cloud chaos resiliency index, availability %, and RTO/RPO compliance."""
    return dr_service.get_resiliency_metrics(property_id=property_id)
