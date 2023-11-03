from typing import Any, Dict, Optional

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

from app_config import AppConfig
from app_logger import AppLogger


class MongoDBClient:
    app_config: AppConfig
    app_logger: AppLogger
    client: Optional[MongoClient] = None

    def __init__(self, app_config: AppConfig, app_logger: AppLogger):
        self.app_config = app_config
        self.app_logger = app_logger

    def connect(self):
        if not self.client:
            uri = self.app_config.get("DEFAULT", "uri")
            self.client = MongoClient(uri, server_api=ServerApi("1"))

            try:
                self.client.admin.command("ping")

            except Exception as error:
                raise Exception from error

    def database_command(self, database_name: str, command: dict):
        database = self.client[database_name]

        database.command(command)

    def collection_create(self, database_name: str, collection_name: str) -> None:
        database = self.client[database_name]

        database.create_collection(
            collection_name
        )

    def collection_drop(self, database_name: str, collection_name: str) -> None:
        database = self.client[database_name]
        collection = database[collection_name]

        collection.drop()

    def collection_find_one(self, database_name: str, collection_name: str, filter: dict):
        try:
            database = self.client[database_name]
            collection = database[collection_name]

            return collection.find_one(filter)

        except Exception as error:
            raise ValueError from error

    def collection_list(self, database_name: str, collection_name: str) -> list:
        database = self.client[database_name]
        collection = database[collection_name]

        all_documents = collection.find({})

        return list(all_documents)

    def collection_insert(self, database_name: str, collection_name: str, data: Dict[str, Any]):
        try:
            database = self.client[database_name]
            collection = database[collection_name]

            return collection.insert_one(data).inserted_id

        except Exception as error:
            raise ValueError from error

    def wix_order_replicate(self, database_name: str, collection_name: str, data_list: list) -> None:
        database = self.client[database_name]
        collection = database[collection_name]

        for obj in data_list:
            # Check if the document with the same ID exists in MongoDB
            existing_document = collection.find_one({"id": obj["id"]})

            if existing_document:
                # Compare lastUpdated dates
                if obj["lastUpdated"] > existing_document["lastUpdated"]:
                    # Update the document in MongoDB
                    collection.update_one(
                        {"_id": existing_document["_id"]}, {"$set": obj})
            else:
                # Insert as a new document in MongoDB
                collection.insert_one(obj)
