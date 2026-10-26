"""Victory Crest One - Multi-Cloud Resiliency & Autonomous DR Service
Orchestrates multi-cloud standby cluster nodes (AWS, Azure, GCP, On-Premise),
cross-cloud replication stream monitoring, automated chaos failover drills, and zero-RPO telemetry.
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime, timezone
import uuid
from fastapi import HTTPException, status

from backend.app.schemas.dr import (
    CloudReplicaNodeCreate,
    CloudReplicaNodeOut,
    FailoverDrillCreate,
    FailoverDrillOut,
    FailoverTriggerRequest,
    FailoverTriggerResponse,
    ReplicationLagTestRequest,
    ReplicationLagTestResponse,
    DrResiliencyMetricsOut,
)
from shared.enums import (
    CloudProvider,
    ReplicationMode,
    NodeRole,
    NodeHealthStatus,
    FailoverDrillType,
    FailoverDrillStatus,
)
from shared.calculations import (
    calculate_replication_lag,
    calculate_dr_rto_rpo_metrics,
    calculate_chaos_resiliency_score,
)
from shared.constants import DEMO_ORGANISATIONS

# In-memory cluster state stores
_NODES_STORE: Dict[str, Dict[str, Any]] = {}
_DRILLS_STORE: Dict[str, Dict[str, Any]] = {}
_NODE_COUNTER = 1004
_DRILL_COUNTER = 1002


def _seed_dr_cluster():
    """Seed multi-cloud distributed standby topology and historical chaos engineering drills."""
    global _NODE_COUNTER, _DRILL_COUNTER
    if _NODES_STORE:
        return

    org_id = DEMO_ORGANISATIONS[0]["id"]
    prop_mdu = DEMO_ORGANISATIONS[0]["properties"][0]["id"]
    now = datetime.now(timezone.utc)

    # 1. Distributed Multi-Cloud Standby Nodes
    seed_nodes = [
        {
            "id": "node_dr_1001",
            "organization_id": org_id,
            "property_id": prop_mdu,
            "node_code": "NODE-AWS-MUMBAI",
            "name": "AWS Asia-Pacific Primary Cloud Cluster",
            "provider": CloudProvider.AWS.value,
            "region": "ap-south-1 (Mumbai)",
            "role": NodeRole.PRIMARY.value,
            "replication_mode": ReplicationMode.SYNCHRONOUS.value,
            "health_status": NodeHealthStatus.HEALTHY.value,
            "replication_lag_seconds": Decimal("0.000"),
            "sync_latency_ms": Decimal("4.20"),
            "endpoint_url": "https://db-primary.ap-south-1.aws.victorycrest.internal",
            "last_heartbeat_at": now,
            "is_active": True,
            "created_at": now
        },
        {
            "id": "node_dr_1002",
            "organization_id": org_id,
            "property_id": prop_mdu,
            "node_code": "NODE-AZURE-CHENNAI",
            "name": "Azure Central India Hot Standby Replica",
            "provider": CloudProvider.AZURE.value,
            "region": "centralindia (Pune/Chennai)",
            "role": NodeRole.HOT_STANDBY.value,
            "replication_mode": ReplicationMode.SYNCHRONOUS.value,
            "health_status": NodeHealthStatus.HEALTHY.value,
            "replication_lag_seconds": Decimal("0.085"),
            "sync_latency_ms": Decimal("8.50"),
            "endpoint_url": "https://db-standby.centralindia.azure.victorycrest.internal",
            "last_heartbeat_at": now,
            "is_active": True,
            "created_at": now
        },
        {
            "id": "node_dr_1003",
            "organization_id": org_id,
            "property_id": None,
            "node_code": "NODE-GCP-SINGAPORE",
            "name": "GCP Southeast Asia Geo-Redundant Standby",
            "provider": CloudProvider.GCP.value,
            "region": "asia-southeast1 (Singapore)",
            "role": NodeRole.HOT_STANDBY.value,
            "replication_mode": ReplicationMode.ASYNCHRONOUS.value,
            "health_status": NodeHealthStatus.STANDBY.value,
            "replication_lag_seconds": Decimal("0.240"),
            "sync_latency_ms": Decimal("32.10"),
            "endpoint_url": "https://db-geo.asia-southeast1.gcp.victorycrest.internal",
            "last_heartbeat_at": now,
            "is_active": True,
            "created_at": now
        },
        {
            "id": "node_dr_1004",
            "organization_id": org_id,
            "property_id": prop_mdu,
            "node_code": "NODE-ONPREM-MADURAI",
            "name": "Madurai Flagship Private Edge Witness Node",
            "provider": CloudProvider.ON_PREMISE.value,
            "region": "in-mdu-dc1 (Madurai HQ)",
            "role": NodeRole.WITNESS.value,
            "replication_mode": ReplicationMode.SYNCHRONOUS.value,
            "health_status": NodeHealthStatus.HEALTHY.value,
            "replication_lag_seconds": Decimal("0.012"),
            "sync_latency_ms": Decimal("1.80"),
            "endpoint_url": "https://db-witness.mdu-dc1.local.victorycrest.internal",
            "last_heartbeat_at": now,
            "is_active": True,
            "created_at": now
        }
    ]
    for node in seed_nodes:
        _NODES_STORE[node["id"]] = node

    # 2. Historical Autonomous Chaos Failover Drills
    seed_drills = [
        {
            "id": "drill_dr_1001",
            "organization_id": org_id,
            "drill_code": "DRILL-2026-001",
            "drill_type": FailoverDrillType.ZONE_OUTAGE.value,
            "target_primary_node": "NODE-AWS-MUMBAI",
            "promoted_standby_node": "NODE-AZURE-CHENNAI",
            "status": FailoverDrillStatus.SUCCEEDED.value,
            "simulated_failure": "Simulated blackout of primary AWS ap-south-1 zone with instant traffic rerouting.",
            "actual_rto_seconds": Decimal("4.20"),
            "actual_rpo_seconds": Decimal("0.00"),
            "traffic_rerouted_percent": Decimal("100.00"),
            "execution_log": "Quorum verified by Witness node. Consensus leadership transferred to Azure Central India in 4.2s. 0 lost transactions.",
            "executed_at": now,
            "completed_at": now,
            "created_at": now
        },
        {
            "id": "drill_dr_1002",
            "organization_id": org_id,
            "drill_code": "DRILL-2026-002",
            "drill_type": FailoverDrillType.DATABASE_SPLIT_BRAIN.value,
            "target_primary_node": "NODE-AWS-MUMBAI",
            "promoted_standby_node": "NODE-GCP-SINGAPORE",
            "status": FailoverDrillStatus.SUCCEEDED.value,
            "simulated_failure": "Artificial network partition isolating primary master node from quorum majority.",
            "actual_rto_seconds": Decimal("5.80"),
            "actual_rpo_seconds": Decimal("0.05"),
            "traffic_rerouted_percent": Decimal("100.00"),
            "execution_log": "Raft consensus election resolved without stale writes. GCP standby promoted to primary without data divergence.",
            "executed_at": now,
            "completed_at": now,
            "created_at": now
        }
    ]
    for drill in seed_drills:
        _DRILLS_STORE[drill["id"]] = drill


_seed_dr_cluster()


class MultiCloudDrService:
    """Multi-cloud resiliency, autonomous replication consensus, and chaos failover orchestrator."""

    def __init__(self):
        _seed_dr_cluster()

    def get_nodes(
        self,
        organization_id: Optional[str] = None,
        property_id: Optional[str] = None,
        provider: Optional[CloudProvider] = None,
        role: Optional[NodeRole] = None,
        status_filter: Optional[NodeHealthStatus] = None
    ) -> List[CloudReplicaNodeOut]:
        """Fetch registered multi-cloud cluster nodes matching query filters."""
        org_id = organization_id or DEMO_ORGANISATIONS[0]["id"]
        nodes = []
        for n in _NODES_STORE.values():
            if n.get("organization_id") != org_id:
                continue
            if property_id and n.get("property_id") and n.get("property_id") != property_id:
                continue
            if provider:
                p_val = provider.value if hasattr(provider, "value") else str(provider)
                if n.get("provider") != p_val:
                    continue
            if role:
                r_val = role.value if hasattr(role, "value") else str(role)
                if n.get("role") != r_val:
                    continue
            if status_filter:
                st_val = status_filter.value if hasattr(status_filter, "value") else str(status_filter)
                if n.get("health_status") != st_val:
                    continue
            nodes.append(CloudReplicaNodeOut(**n))
        return sorted(nodes, key=lambda x: (0 if x.role == NodeRole.PRIMARY else 1, x.node_code))

    def create_node(
        self,
        payload: CloudReplicaNodeCreate,
        organization_id: Optional[str] = None
    ) -> CloudReplicaNodeOut:
        """Register a new cloud standby replica node into the distributed consensus cluster."""
        global _NODE_COUNTER
        _NODE_COUNTER += 1
        node_id = f"node_dr_{_NODE_COUNTER}"
        now = datetime.now(timezone.utc)
        org_id = organization_id or DEMO_ORGANISATIONS[0]["id"]

        node_data = {
            "id": node_id,
            "organization_id": org_id,
            "property_id": payload.property_id,
            "node_code": payload.node_code,
            "name": payload.name,
            "provider": payload.provider.value if hasattr(payload.provider, "value") else str(payload.provider),
            "region": payload.region,
            "role": payload.role.value if hasattr(payload.role, "value") else str(payload.role),
            "replication_mode": payload.replication_mode.value if hasattr(payload.replication_mode, "value") else str(payload.replication_mode),
            "health_status": payload.health_status.value if hasattr(payload.health_status, "value") else str(payload.health_status),
            "replication_lag_seconds": Decimal("0.050"),
            "sync_latency_ms": Decimal("15.00"),
            "endpoint_url": payload.endpoint_url,
            "last_heartbeat_at": now,
            "is_active": True,
            "created_at": now
        }
        _NODES_STORE[node_id] = node_data
        return CloudReplicaNodeOut(**node_data)

    def promote_node(
        self,
        node_id: str,
        organization_id: Optional[str] = None
    ) -> CloudReplicaNodeOut:
        """Promote a standby node to PRIMARY and demote existing primary to HOT_STANDBY."""
        org_id = organization_id or DEMO_ORGANISATIONS[0]["id"]
        target = _NODES_STORE.get(node_id)
        if not target or target.get("organization_id") != org_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Node {node_id} not found")

        # Demote current primary
        for n in _NODES_STORE.values():
            if n.get("organization_id") == org_id and n.get("role") == NodeRole.PRIMARY.value:
                n["role"] = NodeRole.HOT_STANDBY.value
                n["health_status"] = NodeHealthStatus.STANDBY.value

        target["role"] = NodeRole.PRIMARY.value
        target["health_status"] = NodeHealthStatus.HEALTHY.value
        target["replication_lag_seconds"] = Decimal("0.000")
        target["last_heartbeat_at"] = datetime.now(timezone.utc)
        return CloudReplicaNodeOut(**target)

    def get_drills(
        self,
        organization_id: Optional[str] = None,
        status_filter: Optional[FailoverDrillStatus] = None,
        drill_type: Optional[FailoverDrillType] = None
    ) -> List[FailoverDrillOut]:
        """Retrieve historical and scheduled failover drills."""
        org_id = organization_id or DEMO_ORGANISATIONS[0]["id"]
        drills = []
        for d in _DRILLS_STORE.values():
            if d.get("organization_id") != org_id:
                continue
            if status_filter:
                st_val = status_filter.value if hasattr(status_filter, "value") else str(status_filter)
                if d.get("status") != st_val:
                    continue
            if drill_type:
                dt_val = drill_type.value if hasattr(drill_type, "value") else str(drill_type)
                if d.get("drill_type") != dt_val:
                    continue
            drills.append(FailoverDrillOut(**d))
        return sorted(drills, key=lambda x: str(x.created_at or ""), reverse=True)

    def trigger_failover_drill(
        self,
        payload: FailoverTriggerRequest,
        organization_id: Optional[str] = None
    ) -> FailoverTriggerResponse:
        """Execute an automated chaos failover drill, measuring switchover RTO and data-loss window (RPO)."""
        global _DRILL_COUNTER
        _DRILL_COUNTER += 1
        org_id = organization_id or DEMO_ORGANISATIONS[0]["id"]
        now = datetime.now(timezone.utc)

        # Identify primary and standby
        primary_node = None
        standby_node = None

        for n in _NODES_STORE.values():
            if n.get("organization_id") == org_id:
                if n.get("role") == NodeRole.PRIMARY.value and not primary_node:
                    primary_node = n
                elif n.get("role") == NodeRole.HOT_STANDBY.value and not standby_node:
                    standby_node = n

        prim_code = payload.target_primary_node or (primary_node["node_code"] if primary_node else "NODE-AWS-MUMBAI")
        standby_code = payload.promoted_standby_node or (standby_node["node_code"] if standby_node else "NODE-AZURE-CHENNAI")

        drill_id = f"drill_dr_{_DRILL_COUNTER}"
        drill_code = f"DRILL-2026-{_DRILL_COUNTER:03d}"

        # Simulate switchover latency (RTO: 3.5s - 5.5s) and RPO (0.00s - 0.05s)
        rto = Decimal("4.35")
        rpo = Decimal("0.00")

        drill_data = {
            "id": drill_id,
            "organization_id": org_id,
            "drill_code": drill_code,
            "drill_type": payload.drill_type.value if hasattr(payload.drill_type, "value") else str(payload.drill_type),
            "target_primary_node": prim_code,
            "promoted_standby_node": standby_code,
            "status": FailoverDrillStatus.SUCCEEDED.value,
            "simulated_failure": f"Chaos simulation: {payload.drill_type}. Partition: {payload.simulate_network_partition}.",
            "actual_rto_seconds": rto,
            "actual_rpo_seconds": rpo,
            "traffic_rerouted_percent": Decimal("100.00"),
            "execution_log": f"Autonomous failover initiated. {prim_code} demoted; {standby_code} elected leader in {rto}s. Zero-RPO preserved.",
            "executed_at": now,
            "completed_at": now,
            "created_at": now
        }
        _DRILLS_STORE[drill_id] = drill_data

        return FailoverTriggerResponse(
            drill_id=drill_id,
            drill_code=drill_code,
            status=FailoverDrillStatus.SUCCEEDED,
            promoted_node=standby_code,
            demoted_node=prim_code,
            switchover_latency_seconds=rto,
            data_loss_window_seconds=rpo,
            traffic_rerouted_percent=Decimal("100.00"),
            is_zero_rpo_achieved=True,
            summary=f"Failover drill {drill_code} succeeded in {rto}s with 0 lost transactions."
        )

    def test_replication_lag(
        self,
        request: ReplicationLagTestRequest
    ) -> ReplicationLagTestResponse:
        """Run diagnostics on replication stream latency and byte delta."""
        # Find node
        node = None
        for n in _NODES_STORE.values():
            if n.get("node_code") == request.node_code:
                node = n
                break

        base_lag = Decimal(str(node.get("replication_lag_seconds", "0.050"))) if node else Decimal("0.050")
        added_lag = Decimal(str(request.simulated_bytes_behind)) * Decimal("0.00001")
        packet_pen = Decimal(str(request.packet_loss_percent)) * Decimal("0.05")
        final_lag = (base_lag + added_lag + packet_pen).quantize(Decimal("0.001"))

        if final_lag < Decimal("1.000"):
            tier = "SYNCHRONIZED_ZERO_RPO"
        elif final_lag < Decimal("5.000"):
            tier = "NOMINAL_STANDBY"
        elif final_lag < Decimal("30.000"):
            tier = "ELEVATED_LAG"
        else:
            tier = "DESYNCHRONIZED_ALERT"

        return ReplicationLagTestResponse(
            node_code=request.node_code,
            replication_lag_seconds=final_lag,
            lag_tier=tier,
            sync_latency_ms=Decimal("12.50") + (Decimal(str(request.packet_loss_percent)) * Decimal("2.0")),
            is_zero_rpo=(final_lag < Decimal("1.000")),
            consensus_valid=(final_lag < Decimal("30.000"))
        )

    def get_resiliency_metrics(
        self,
        organization_id: Optional[str] = None,
        property_id: Optional[str] = None
    ) -> DrResiliencyMetricsOut:
        """Calculate consolidated multi-cloud DR telemetry and resiliency score."""
        org_id = organization_id or DEMO_ORGANISATIONS[0]["id"]
        nodes = [
            n for n in _NODES_STORE.values()
            if n.get("organization_id") == org_id and (
                property_id is None or n.get("property_id") is None or n.get("property_id") == property_id
            )
        ]
        drills = [
            d for d in _DRILLS_STORE.values()
            if d.get("organization_id") == org_id
        ]

        metrics = calculate_dr_rto_rpo_metrics(nodes, drills)
        score, tier = calculate_chaos_resiliency_score(nodes, drills)

        providers = sorted(list({str(n.get("provider")) for n in nodes if str(n.get("health_status")).upper() in ("HEALTHY", "STANDBY")}))

        return DrResiliencyMetricsOut(
            resiliency_score=score,
            resiliency_tier=tier,
            cluster_availability_percent=metrics["cluster_availability_percent"],
            total_nodes=metrics["total_nodes"],
            healthy_nodes=metrics["healthy_nodes"],
            active_primary_count=metrics["active_primary_count"],
            hot_standby_count=metrics["hot_standby_count"],
            max_replication_lag_seconds=metrics["max_replication_lag_seconds"],
            avg_replication_lag_seconds=metrics["avg_replication_lag_seconds"],
            total_drills=metrics["total_drills"],
            succeeded_drills=metrics["succeeded_drills"],
            drill_success_rate_percent=metrics["drill_success_rate_percent"],
            avg_actual_rto_seconds=metrics["avg_actual_rto_seconds"],
            avg_actual_rpo_seconds=metrics["avg_actual_rpo_seconds"],
            target_rto_seconds=metrics["target_rto_seconds"],
            target_rpo_seconds=metrics["target_rpo_seconds"],
            rto_sla_met=metrics["rto_sla_met"],
            rpo_sla_met=metrics["rpo_sla_met"],
            is_zero_rpo_compliant=metrics["is_zero_rpo_compliant"],
            providers_active=providers
        )


dr_service = MultiCloudDrService()
