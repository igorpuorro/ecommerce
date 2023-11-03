from typing import List, Optional

from itertools import compress

import json
import requests

from app_config import AppConfig
from app_logger import AppLogger
from wix_client import WixClient
from wix_data import FilterOperator, FulfillmentStatus, PaymentStatus, OrderFulfillment, OrderQueryFilter, OrderQuerySort


class WixOrderHandler:
    app_config: AppConfig
    app_logger: AppLogger
    wix_client: WixClient

    order_query_response: Optional[dict] = None
    order_number_list_string: Optional[str] = None

    def __init__(self, app_config: AppConfig, app_logger: AppLogger):
        self.app_config = app_config
        self.wix_client = WixClient(app_config, app_logger)

    def get_data_collections(self):
        return self.wix_client.get_wix_data_v2_collections()

    def get_order(self, order_number: str) -> dict:
        try:
            for order in self.order_query_response.get("orders"):
                if str(order.get("number")) == order_number:
                    return order

        except Exception:
            return {}

    def get_order_list(self) -> List[dict]:
        try:
            return self.order_query_response.get("orders", [])

        except Exception:
            return []

    def get_order_list_total_results(self) -> int:
        return self.order_query_response.get("totalResults", 0)

    def get_order_number_list_string(self) -> str:
        if isinstance(self.order_number_list_string, str):
            return self.order_number_list_string

        order_list = self.get_order_list()
        order_number_list = sorted([item.get("number") for item in order_list])

        if len(order_number_list) == 0:
            return ""

        sequence = []
        current_sequence = [order_number_list[0]]

        for i in range(1, len(order_number_list)):
            num = int(order_number_list[i])
            prev_num = int(order_number_list[i - 1])

            if num - prev_num == 1:
                current_sequence.append(str(num))
            else:
                sequence.append(current_sequence)
                current_sequence = [str(num)]

        sequence.append(current_sequence)

        result = ""

        for s in sequence:
            if len(s) > 1:
                result += f"{s[0]} - {s[-1]}, "
            else:
                result += f"{s[0]}, "

        self.order_number_list_string = result.rstrip(", ")

        return self.order_number_list_string

    def order_fulfillment_create(self, order_id: str, order_fulfillment: OrderFulfillment) -> None:
        self.wix_client.post_stores_v2_orders_fulfillments(
            order_id,
            order_fulfillment
        )

    def order_fulfillment_delete(self, order_id: str, fulfillment_id: str) -> None:
        self.wix_client.delete_stores_v2_orders_fulfillments(
            order_id,
            fulfillment_id
        )

    def order_query(self, order_query_filter: OrderQueryFilter, order_query_sort: OrderQuerySort) -> None:
        self.order_query_response = self.wix_client.post_stores_v2_orders_query(
            order_query_filter, order_query_sort
        )
