"""Módulo de infraestrutura e integração com banco de dados Supabase."""

from app.infrastructure.supabase.client import (
    SupabaseClientManager,
    get_supabase_admin_client,
    get_supabase_client,
)
from app.infrastructure.supabase.config import SupabaseConfig
from app.infrastructure.supabase.exceptions import (
    SupabaseConfigurationError,
    SupabaseConnectionError,
    SupabaseIntegrationError,
    SupabaseQueryError,
    SupabaseRecordNotFoundError,
)
from app.infrastructure.supabase.repository import (
    SupabaseBaseRepository,
    SupabaseFertilizerRepository,
    SupabaseRawDataRepository,
)

__all__ = [
    "SupabaseConfig",
    "SupabaseClientManager",
    "get_supabase_client",
    "get_supabase_admin_client",
    "SupabaseBaseRepository",
    "SupabaseRawDataRepository",
    "SupabaseFertilizerRepository",
    "SupabaseIntegrationError",
    "SupabaseConfigurationError",
    "SupabaseConnectionError",
    "SupabaseQueryError",
    "SupabaseRecordNotFoundError",
]
