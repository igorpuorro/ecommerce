import json

import requests

from requests import Response
from requests.exceptions import RequestException

from app_config import AppConfig
from app_logger import AppLogger
from wix_data import FilterOperator, FulfillmentStatus, PaymentStatus, OrderFulfillment, OrderQueryFilter, OrderQuerySort


class WixClient:
    app_config: AppConfig
    app_logger: AppLogger

    def __init__(self, app_config: AppConfig, app_logger: AppLogger):
        self.app_config = app_config
        self.app_logger = app_logger

    def _add_headers(self, headers: dict) -> None:
        headers["Authorization"] = self.app_config.get(
            "DEFAULT", "Authorization"
        )
        headers["wix-account-id"] = self.app_config.get(
            "DEFAULT", "wix-account-id"
        )
        headers["wix-site-id"] = self.app_config.get(
            "DEFAULT", "wix-site-id"
        )

    def _delete_request(self, url, headers) -> Response:
        try:
            response = requests.delete(
                url, headers=headers, timeout=10
            )

            response.raise_for_status()

            return response

        except requests.exceptions.RequestException as e:
            print(f"Error making API request: {e}")

    def _get_request(self, url, headers) -> Response:
        try:
            response = requests.get(
                url, headers=headers, timeout=10
            )

            response.raise_for_status()

            return response

        except requests.exceptions.RequestException as e:
            print(f"Error making API request: {e}")

    def _post_request(self, url, headers, data) -> Response:
        try:
            response = requests.post(
                url, headers=headers, json=data, timeout=10
            )

            response.raise_for_status()

            return response

        except requests.exceptions.RequestException as e:
            print(f"Error making API request: {e}")

    def get_wix_data_v2_collections(self) -> dict:
        base_url = self.app_config.get("DEFAULT", "base_url")
        url = f"{base_url}/wix-data/v2/collections"

        headers = {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json"
        }

        self._add_headers(headers)

        try:
            response = self._get_request(url, headers)

            if response.status_code == 200:
                return response.json()

            raise RequestException()

        except RequestException as error:
            raise RequestException() from error

    def delete_stores_v2_orders_fulfillments(self, order_id: str, fulfillment_id: str) -> dict:
        base_url = self.app_config.get("DEFAULT", "base_url")
        url = f"{base_url}/stores/v2/orders/{order_id}/fulfillments/{fulfillment_id}"

        headers = {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json"
        }

        self._add_headers(headers)

        try:
            response = self._delete_request(url, headers)

            if response.status_code == 200:
                self.app_logger.log_request_response(
                    response
                )

                return response.json()

            raise RequestException()

        except RequestException as error:
            raise RequestException() from error

    def post_stores_v2_orders_fulfillments(self, order_id: str, order_fulfillment: OrderFulfillment) -> dict:
        base_url = self.app_config.get("DEFAULT", "base_url")
        url = f"{base_url}/stores/v2/orders/{order_id}/fulfillments"

        headers = {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json"
        }

        self._add_headers(headers)

        data = {
            "fulfillment": {
                "lineItems": order_fulfillment.line_items,
                "trackingInfo": {
                    "shippingProvider": order_fulfillment.tracking_info_shipping_provider,
                    "trackingNumber": order_fulfillment.tracking_info_tracking_number,
                    "trackingLink": order_fulfillment.tracking_info_tracking_link
                }
            }
        }

        try:
            response = self._post_request(url, headers, data)

            if response.status_code == 200:
                self.app_logger.log_request_response(
                    response
                )

                return response.json()

            raise RequestException()

        except RequestException as error:
            raise RequestException() from error

    def post_stores_v2_orders_query(self, order_query_filter: OrderQueryFilter, order_query_sort: OrderQuerySort = OrderQuerySort.NUMBER_ASC) -> dict:
        base_url = self.app_config.get("DEFAULT", "base_url")
        url = f"{base_url}/stores/v2/orders/query"

        headers = {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json"
        }

        self._add_headers(headers)

        query_filter_dict = {}

        if isinstance(order_query_filter.last_updated, dict):
            last_updated_operator, last_updated_timestamp = list(
                order_query_filter.last_updated.items()
            )[0]

            query_filter_dict["lastUpdated"] = {
                last_updated_operator.value: last_updated_timestamp
            }

        if isinstance(order_query_filter.date_created, dict):
            date_created_operator, date_created_timestamp = list(
                order_query_filter.date_created.items()
            )[0]

            query_filter_dict["dateCreated"] = {
                date_created_operator.value: date_created_timestamp
            }

        if isinstance(order_query_filter.number_list, list):
            query_filter_dict["number"] = {
                "$hasSome": order_query_filter.number_list
            }

        if isinstance(order_query_filter.read, bool):
            query_filter_dict["read"] = str(order_query_filter.read).lower()

        if isinstance(order_query_filter.archived, bool):
            query_filter_dict["archived"] = str(
                order_query_filter.archived
            ).lower()

        if isinstance(order_query_filter.payment_status, PaymentStatus):
            query_filter_dict["paymentStatus"] = order_query_filter.payment_status.value

        if isinstance(order_query_filter.fulfillment_status, FulfillmentStatus):
            query_filter_dict["fulfillmentStatus"] = order_query_filter.fulfillment_status.value

        data = {
            "query": {
                "filter": json.dumps(query_filter_dict),
                "paging": {
                    "limit": 100
                },
                "sort": json.dumps([order_query_sort.value])
            }
        }

        try:
            response = self._post_request(url, headers, data)

            if response.status_code == 200:
                return response.json()

            raise RequestException()

        except RequestException as error:
            raise RequestException() from error
