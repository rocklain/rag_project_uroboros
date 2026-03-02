import asyncio
import os
from azure.cosmos.aio import CosmosClient
from azure.cosmos import PartitionKey, exceptions
from .uroboros_engine import settings


class CosmosDBManager:
    def __init__(self):
        self.client = CosmosClient(
            settings.azure_cosmos_endpoint, settings.azure_cosmos_key
        )
        self.database_name = settings.azure_cosmos_database_name
        self.container_name = settings.azure_cosmos_container_name
        self.database = None
        self.container = None

    async def _get_or_create_container(self):
        if self.container:
            return self.container

        try:
            self.database = self.client.get_database_client(self.database_name)
            await self.database.read()
        except exceptions.CosmosResourceNotFoundError:
            print(f"Database '{self.database_name}' not found. Creating it...")
            self.database = await self.client.create_database(self.database_name)

        try:
            self.container = self.database.get_container_client(self.container_name)
            await self.container.read()
            return self.container
        except exceptions.CosmosResourceNotFoundError:
            print(
                f"Container '{self.container_name}' not found. Creating it with partition key /id..."
            )
            self.container = await self.database.create_container(
                id=self.container_name, partition_key=PartitionKey(path="/id")
            )
            return self.container

    async def add_item(self, item_data: dict):
        """Adds an item to the Cosmos DB container."""
        container = await self._get_or_create_container()
        try:
            response = await container.upsert_item(body=item_data)
            print(f"Successfully upserted item with id: {response.get('id')}")
            return response
        except exceptions.CosmosHttpResponseError as e:
            print(f"Error adding item to Cosmos DB: {e}")
            raise

    async def get_items(self):
        """Retrieves all items from the container, ordered by timestamp descending."""
        container = await self._get_or_create_container()
        try:
            # TODO 全データ呼び出しとしているので将来的にページング処理を実装する
            query = "SELECT * FROM c ORDER BY c._ts DESC"
            items = [
                item async for item in container.query_items(query=query)
            ]
            return items
        except exceptions.CosmosHttpResponseError as e:
            print(f"Error getting items from Cosmos DB: {e}")
            raise

    async def delete_item(self, item_id: str):
        """Deletes an item from the container."""
        container = await self._get_or_create_container()
        try:
            await container.delete_item(item=item_id, partition_key=item_id)
            print(f"Successfully deleted item with id: {item_id}")
        except exceptions.CosmosHttpResponseError as e:
            print(f"Error deleting item from Cosmos DB: {e}")
            raise


# シングルトンインスタンス
cosmos_manager = CosmosDBManager()
