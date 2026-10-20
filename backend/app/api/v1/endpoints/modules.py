"""Victory Crest One - Module Catalog Endpoints
Provides system module metadata, phase status, active capabilities, and navigation links.
"""

from typing import List, Dict, Any
from fastapi import APIRouter
from shared.constants import MODULE_CATALOG
from shared.dto import ModuleInfo

router = APIRouter()


@router.get(
    "/modules",
    response_model=List[ModuleInfo],
    summary="List System Modules",
    description="Returns metadata and current operational status of all business modules."
)
def get_modules():
    return [ModuleInfo(**m) for m in MODULE_CATALOG]
