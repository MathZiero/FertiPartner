"""Base and specialized repositories for Supabase table operations."""

import logging
from typing import Any, cast
from supabase import Client

from app.infrastructure.supabase.client import get_supabase_client
from app.infrastructure.supabase.config import SupabaseConfig
from app.infrastructure.supabase.exceptions import (
    SupabaseQueryError,
    SupabaseRecordNotFoundError,
)

logger = logging.getLogger(__name__)


class SupabaseBaseRepository:
    """Generic base repository providing CRUD and query operations over a Supabase table."""

    def __init__(
        self,
        table_name: str,
        client: Client | None = None,
        config: SupabaseConfig | None = None,
    ) -> None:
        self.table_name = table_name
        self._client = client or get_supabase_client(config)

    @property
    def client(self) -> Client:
        """Get the underlying Supabase client."""
        return self._client

    def insert(self, data: dict[str, Any]) -> dict[str, Any]:
        """Insert a single record into the table.

        Args:
            data: Dictionary containing row values.

        Returns:
            dict[str, Any]: Inserted record returned from the database.

        Raises:
            SupabaseQueryError: If the insert operation fails.
        """
        try:
            response = self.client.table(self.table_name).insert(data).execute()
            if response.data:
                return cast(dict[str, Any], response.data[0])
            return data
        except Exception as exc:
            logger.error("Error inserting into table %s: %s", self.table_name, exc)
            raise SupabaseQueryError(
                f"Error executing operation on table {self.table_name}: {exc}"
            ) from exc

    def insert_many(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Insert multiple records into the table in bulk.

        Args:
            items: List of dictionaries to insert.

        Returns:
            list[dict[str, Any]]: Inserted records.

        Raises:
            SupabaseQueryError: If the bulk insert operation fails.
        """
        if not items:
            return []
        try:
            response = self.client.table(self.table_name).insert(items).execute()
            return cast(list[dict[str, Any]], response.data) if response.data else []
        except Exception as exc:
            logger.error("Error bulk inserting into table %s: %s", self.table_name, exc)
            raise SupabaseQueryError(
                f"Error executing operation on table {self.table_name}: {exc}"
            ) from exc

    def find_by_id(
        self, id_value: str | int, id_column: str = "id"
    ) -> dict[str, Any] | None:
        """Find a record by its identifier column.

        Args:
            id_value: The ID value to match.
            id_column: Name of the identifier column (default: "id").

        Returns:
            dict[str, Any] | None: The found record, or None if not found.

        Raises:
            SupabaseQueryError: If the query fails.
        """
        try:
            query = (
                self.client.table(self.table_name)
                .select("*")
                .eq(id_column, id_value)
                .limit(1)
            )
            response = query.execute()
            if response.data and len(response.data) > 0:
                return cast(dict[str, Any], response.data[0])
            return None
        except Exception as exc:
            logger.error(
                "Error finding record %s=%s in %s: %s",
                id_column,
                id_value,
                self.table_name,
                exc,
            )
            raise SupabaseQueryError(
                f"Error executing operation on table {self.table_name}: {exc}"
            ) from exc

    def find_all(
        self,
        limit: int = 100,
        offset: int = 0,
        order_by: str | None = None,
        ascending: bool = True,
    ) -> list[dict[str, Any]]:
        """Retrieve a paginated list of records.

        Args:
            limit: Maximum number of records to return.
            offset: Starting index for pagination.
            order_by: Optional column name to sort by.
            ascending: Sort order (True for ascending, False for descending).

        Returns:
            list[dict[str, Any]]: List of retrieved records.

        Raises:
            SupabaseQueryError: If the query fails.
        """
        try:
            query = self.client.table(self.table_name).select("*")
            if order_by:
                query = query.order(order_by, desc=not ascending)

            # Supabase range is inclusive [start, end]
            end_index = offset + limit - 1
            query = query.range(offset, end_index)
            response = query.execute()
            return cast(list[dict[str, Any]], response.data) if response.data else []
        except Exception as exc:
            logger.error("Error listing records from %s: %s", self.table_name, exc)
            raise SupabaseQueryError(
                f"Error executing operation on table {self.table_name}: {exc}"
            ) from exc

    def find_where(
        self, filters: dict[str, Any], limit: int = 100
    ) -> list[dict[str, Any]]:
        """Query records matching exact equality filters.

        Args:
            filters: Dictionary of column-value pairs to filter by.
            limit: Maximum number of records to return.

        Returns:
            list[dict[str, Any]]: Matching records.

        Raises:
            SupabaseQueryError: If the query fails.
        """
        try:
            query = self.client.table(self.table_name).select("*")
            for column, value in filters.items():
                query = query.eq(column, value)
            query = query.limit(limit)
            response = query.execute()
            return cast(list[dict[str, Any]], response.data) if response.data else []
        except Exception as exc:
            logger.error(
                "Error querying %s with filters %s: %s", self.table_name, filters, exc
            )
            raise SupabaseQueryError(
                f"Error executing operation on table {self.table_name}: {exc}"
            ) from exc

    def update(
        self,
        id_value: str | int,
        data: dict[str, Any],
        id_column: str = "id",
    ) -> dict[str, Any]:
        """Update a single record by its identifier.

        Args:
            id_value: ID value of the record to update.
            data: Dictionary of fields to update.
            id_column: Column name used as identifier.

        Returns:
            dict[str, Any]: Updated record data.

        Raises:
            SupabaseRecordNotFoundError: If the record does not exist.
            SupabaseQueryError: If the update operation fails.
        """
        try:
            response = (
                self.client.table(self.table_name)
                .update(data)
                .eq(id_column, id_value)
                .execute()
            )
            if not response.data:
                raise SupabaseRecordNotFoundError(
                    f"Record with {id_column} {id_value} not found in table {self.table_name}."
                )
            return cast(dict[str, Any], response.data[0])
        except SupabaseRecordNotFoundError:
            raise
        except Exception as exc:
            logger.error(
                "Error updating %s (%s=%s): %s",
                self.table_name,
                id_column,
                id_value,
                exc,
            )
            raise SupabaseQueryError(
                f"Error executing operation on table {self.table_name}: {exc}"
            ) from exc

    def delete(self, id_value: str | int, id_column: str = "id") -> bool:
        """Delete a record by its identifier.

        Args:
            id_value: ID value of the record to delete.
            id_column: Column name used as identifier.

        Returns:
            bool: True if the record was successfully deleted.

        Raises:
            SupabaseQueryError: If the delete operation fails.
        """
        try:
            response = (
                self.client.table(self.table_name)
                .delete()
                .eq(id_column, id_value)
                .execute()
            )
            return bool(response.data)
        except Exception as exc:
            logger.error(
                "Error deleting from %s (%s=%s): %s",
                self.table_name,
                id_column,
                id_value,
                exc,
            )
            raise SupabaseQueryError(
                f"Error executing operation on table {self.table_name}: {exc}"
            ) from exc


class SupabaseRawDataRepository(SupabaseBaseRepository):
    """Repository specialized in raw datasets ingestion (RD08)."""

    def __init__(
        self,
        client: Client | None = None,
        config: SupabaseConfig | None = None,
    ) -> None:
        super().__init__(table_name="raw_data", client=client, config=config)

    def save_raw_payload(
        self,
        source_id: str,
        collected_at: str,
        reference_date: str,
        raw_payload: dict[str, Any] | list[Any],
        status: str = "RAW",
    ) -> dict[str, Any]:
        """Save an unformatted raw payload into the raw_data table."""
        payload = {
            "source_id": source_id,
            "collected_at": collected_at,
            "reference_date": reference_date,
            "raw_payload": raw_payload,
            "status": status,
        }
        return self.insert(payload)

    def find_by_source(self, source_id: str, limit: int = 100) -> list[dict[str, Any]]:
        """Retrieve recent raw data for a specific source."""
        return self.find_where({"source_id": source_id}, limit=limit)


class SupabaseFertilizerRepository(SupabaseBaseRepository):
    """Repository specialized in fertilizer entities and catalog (RD01)."""

    def __init__(
        self,
        client: Client | None = None,
        config: SupabaseConfig | None = None,
    ) -> None:
        super().__init__(table_name="fertilizers", client=client, config=config)

    def find_by_name(self, name: str) -> dict[str, Any] | None:
        """Find fertilizer by name."""
        results = self.find_where({"name": name}, limit=1)
        return results[0] if results else None

    def find_by_category(self, category: str) -> list[dict[str, Any]]:
        """Find all fertilizers in a given category."""
        return self.find_where({"category": category})
