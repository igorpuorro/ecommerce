import json
import os
import time

from app_config import AppConfig
from app_logger import AppLogger
from cws_data import PrePostagemModalidadePagamento, PrePostagemQueryFilter, PrePostagemStatus, PrePostagemTipoObjeto
from cws_handler import CwsHandler
from ecommerce import Ecommerce
from mongodb_handler import MongoDBHandler
from wsa_handler import WsaHandler
from wix_data import FilterOperator, FulfillmentStatus, PaymentStatus, OrderFulfillment, OrderQueryFilter, OrderQuerySort
from wix_order_handler import WixOrderHandler


if __name__ == "__main__":
    app_logger = AppLogger(
        os.path.join("log", "request_response.log")
    )

    cws_handler = CwsHandler(
        AppConfig(os.path.join("config", "cws.json")),
        "PRODUCAO",
        app_logger
    )

    mongodb_handler = MongoDBHandler(
        AppConfig(os.path.join("config", "mongodb.json")),
        app_logger
    )

    wsa_handler = WsaHandler(
        AppConfig(os.path.join("config", "wsa.json")),
        app_logger
    )

    wix_order_handler = WixOrderHandler(
        AppConfig(os.path.join("config", "wix.json")),
        app_logger
    )

    ecommerce = Ecommerce(
        cws_handler,
        mongodb_handler,
        wsa_handler,
        wix_order_handler
    )
