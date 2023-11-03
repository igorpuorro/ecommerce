import json
import requests

from retrying import retry

from app_config import AppConfig
from app_logger import AppLogger


class WsaClient:
    app_config: AppConfig
    app_logger: AppLogger

    def __init__(self, app_config: AppConfig, app_logger: AppLogger):
        self.app_config = app_config
        self.app_logger = app_logger

    @retry(wait_fixed=600, stop_max_attempt_number=1)
    def _post_request(self, url, headers, data):
        try:
            response = requests.post(
                url, headers=headers, json=data, timeout=300
            )

            self.app_logger.log_request_response(
                response
            )

            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"Error making API request: {e}")

            return None

    def post_correios_enderecador_encomendas(self, request_data: dict):
        base_url = self.app_config.get("DEFAULT", "base_url")
        url = f"{base_url}/correios/enderecador/encomendas"

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*"
        }

        response = self._post_request(url, headers, request_data)

        if response:
            return response
