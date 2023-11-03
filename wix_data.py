from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class FilterOperator(Enum):
    EQ = "$eq"
    NE = "$ne"
    HAS_SOME = "$hasSome"
    LT = "$lt"
    LTE = "$lte"
    GT = "$gt"
    GTE = "$gte"


class FulfillmentStatus(Enum):
    FULFILLED = "FULFILLED"
    NOT_FULFILLED = "NOT_FULFILLED"
    CANCELED = "CANCELED"
    PARTIALLY_FULFILLED = "PARTIALLY_FULFILLED"


class OrderQuerySort(Enum):
    DATE_CREATED_ASC = {"dateCreated": "asc"}
    DATE_CREATED_DESC = {"dateCreated": "desc"}
    LAST_UPDATED_ASC = {"lastUpdated": "asc"}
    LAST_UPDATED_DESC = {"lastUpdated": "desc"}
    NUMBER_ASC = {"number": "asc"}
    NUMBER_DESC = {"number": "desc"}


class PaymentStatus(Enum):
    UNSPECIFIED_PAYMENT_STATUS = "UNSPECIFIED_PAYMENT_STATUS"
    PENDING = "PENDING"
    NOT_PAID = "NOT_PAID"
    PAID = "PAID"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"
    FULLY_REFUNDED = "FULLY_REFUNDED"
    PARTIALLY_PAID = "PARTIALLY_PAID"


@dataclass
class OrderFulfillment:
    tracking_info_shipping_provider: str
    tracking_info_tracking_number: str
    tracking_info_tracking_link: str
    line_items: list

    def to_dict(self):
        pass


@dataclass
class OrderQueryFilter:
    date_created: Optional[Dict[FilterOperator, str]] = None
    last_updated: Optional[Dict[FilterOperator, str]] = None
    number_list: List[str] = None
    read: Optional[bool] = None
    archived: Optional[bool] = None
    payment_status: Optional[PaymentStatus] = None
    fulfillment_status: Optional[FulfillmentStatus] = None

    def to_dict(self):
        pass
