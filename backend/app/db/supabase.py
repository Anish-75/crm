import logging
from typing import Optional
from supabase import Client, create_client
from app.config import get_settings

logger = logging.getLogger(__name__)

_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """
    Get or initialize the singleton Supabase client using the service role key.
    The service role key bypasses RLS on the server side as defined in PRD Section 3.
    """
    global _supabase_client
    if _supabase_client is None:
        settings = get_settings()
        logger.info("Initializing Supabase client with service role key")
        _supabase_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY,
        )
    return _supabase_client


def set_supabase_client(client: Optional[Client]) -> None:
    """Set or override the Supabase client (primarily for testing)."""
    global _supabase_client
    _supabase_client = client

