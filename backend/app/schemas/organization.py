"""Victory Crest One - Organization & Property Schemas
"""

from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class PropertyBase(BaseModel):
    id: str
    code: str
    name: str
    property_type: str = Field(default="hotel", alias="type")
    status: str = "active"
    city: str
    state: str
    country: str = "India"
    rooms_count: int = 0
    is_simulated: bool = False

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class PropertyOut(PropertyBase):
    organization_id: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class OrganizationBase(BaseModel):
    id: str
    code: str
    name: str
    legal_name: str
    currency: str = "INR"
    is_active: bool = True
    is_simulated: bool = False

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class OrganizationOut(OrganizationBase):
    properties: List[PropertyBase] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
