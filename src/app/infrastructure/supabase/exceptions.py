"""Exceções customizadas para operações e integração com o Supabase."""


class SupabaseIntegrationError(Exception):
    """Base exception for all Supabase integration errors."""


class SupabaseConfigurationError(SupabaseIntegrationError):
    """Raised when Supabase settings or environment variables are missing or invalid."""


class SupabaseConnectionError(SupabaseIntegrationError):
    """Raised when Supabase client creation or connection fails."""


class SupabaseQueryError(SupabaseIntegrationError):
    """Raised when a PostgREST table operation or database query fails."""


class SupabaseRecordNotFoundError(SupabaseIntegrationError):
    """Raised when an expected database record is not found."""
