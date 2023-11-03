from typing import List

from itertools import compress

import json
import requests

from app_config import AppConfig
from app_logger import AppLogger
from wsa_client import WsaClient


class WsaHandler:
    app_config: AppConfig
    app_logger: AppLogger
    wsa_client: WsaClient

    def __init__(self, app_config: AppConfig, app_logger: AppLogger):
        self.app_config = app_config
        self.wsa_client = WsaClient(app_config, app_logger)

    def correios_enderecador_encomendas(self, remetente_destinatario_list_dict: dict):
        return self.wsa_client.post_correios_enderecador_encomendas(
            remetente_destinatario_list_dict
        )
