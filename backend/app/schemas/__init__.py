"""Victory Crest One - API Schemas Package
"""

from backend.app.schemas.health import SystemHealthSchema, DatabaseHealthSchema
from backend.app.schemas.organization import OrganizationBase, OrganizationOut, PropertyBase, PropertyOut
from backend.app.schemas.finance import (
    AccountCreate, AccountOut,
    JournalEntryCreate, JournalEntryOut,
    CustomerInvoiceCreate, CustomerInvoiceOut, CustomerPaymentCreate, CustomerPaymentOut,
    SupplierBillCreate, SupplierBillOut, BillPaymentCreate, BillPaymentOut,
    TrialBalanceResponse, ProfitAndLossResponse, BalanceSheetResponse
)
from backend.app.schemas.crm import (
    LeadCreate, LeadUpdate, LeadOut, LeadConvertRequest, LeadConvertResponse,
    DealCreate, DealUpdate, DealOut, DealStageUpdateRequest,
    QuoteCreate, QuoteOut, QuoteConvertInvoiceResponse,
    SalesActivityCreate, SalesActivityOut,
    SalesPipelineMetricsResponse
)

__all__ = [
    "SystemHealthSchema",
    "DatabaseHealthSchema",
    "OrganizationBase",
    "OrganizationOut",
    "PropertyBase",
    "PropertyOut",
    "AccountCreate",
    "AccountOut",
    "JournalEntryCreate",
    "JournalEntryOut",
    "CustomerInvoiceCreate",
    "CustomerInvoiceOut",
    "CustomerPaymentCreate",
    "CustomerPaymentOut",
    "SupplierBillCreate",
    "SupplierBillOut",
    "BillPaymentCreate",
    "BillPaymentOut",
    "TrialBalanceResponse",
    "ProfitAndLossResponse",
    "BalanceSheetResponse",
    "LeadCreate",
    "LeadUpdate",
    "LeadOut",
    "LeadConvertRequest",
    "LeadConvertResponse",
    "DealCreate",
    "DealUpdate",
    "DealOut",
    "DealStageUpdateRequest",
    "QuoteCreate",
    "QuoteOut",
    "QuoteConvertInvoiceResponse",
    "SalesActivityCreate",
    "SalesActivityOut",
    "SalesPipelineMetricsResponse"
]


