from typing import Any, Dict

from app_config import AppConfig
from app_logger import AppLogger
from mongodb_client import MongoDBClient


class MongoDBHandler:
    app_config: AppConfig
    app_logger: AppLogger
    mongodb_client: MongoDBClient

    def __init__(self, app_config: AppConfig, app_logger: AppLogger):
        self.app_config = app_config
        self.mongodb_client = MongoDBClient(app_config, app_logger)

    def collection_create(self, database_name: str, collection_name: str):
        self.mongodb_client.connect()

        self.mongodb_client.collection_create(
            database_name, collection_name
        )

    def collection_drop(self, database_name: str, collection_name: str):
        self.mongodb_client.connect()

        self.mongodb_client.collection_drop(
            database_name, collection_name
        )

    def collection_find_one(self, database_name: str, collection_name: str, filter: dict):
        self.mongodb_client.connect()

        return self.mongodb_client.collection_find_one(
            database_name, collection_name, filter
        )

    def collection_list(self, database_name: str, collection_name: str):
        self.mongodb_client.connect()

        return self.mongodb_client.collection_list(
            database_name, collection_name
        )

    def collection_insert(self, database_name: str, collection_name: str, data: Dict[str, Any]):
        self.mongodb_client.connect()

        return self.mongodb_client.collection_insert(
            database_name, collection_name, data=data
        )

    def wix_order_replicate(self, database_name: str, collection_name: str, data_list: list):
        self.mongodb_client.connect()

        self.mongodb_client.wix_order_replicate(
            database_name, collection_name, data_list=data_list
        )
