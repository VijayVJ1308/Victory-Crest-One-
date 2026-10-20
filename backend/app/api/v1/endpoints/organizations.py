"""Victory Crest One - Organization & Property Endpoints
Provides multi-tenant organization context, properties, and branches.
"""

from typing import List
from fastapi import APIRouter
from shared.constants import DEMO_ORGANISATIONS
from backend.app.schemas.organization import OrganizationOut, PropertyBase

router = APIRouter()


@router.get(
    "/organizations",
    response_model=List[OrganizationOut],
    summary="List Organizations and Properties",
    description="Returns available organizations and associated properties/branches for multi-tenant switching."
)
def get_organizations():
    """Return configured organizations and properties."""
    # Returns the structured organizations catalogue (marked is_simulated where applicable)
    results = []
    for org in DEMO_ORGANISATIONS:
        props = [PropertyBase(**p) for p in org.get("properties", [])]
        results.append(
            OrganizationOut(
                id=org["id"],
                code=org["code"],
                name=org["name"],
                legal_name=org["legal_name"],
                currency=org.get("currency", "INR"),
                is_active=True,
                is_simulated=org.get("is_simulated", True),
                properties=props
            )
        )
    return results
