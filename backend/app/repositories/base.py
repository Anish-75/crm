from typing import Optional
from supabase import Client
from app.db.supabase import get_supabase_client


class BaseRepository:
    """Base repository with access to the Supabase client using the service role key."""

    def __init__(self, client: Optional[Client] = None):
        self._client = client

    @property
    def client(self) -> Client:
        if self._client is None:
            self._client = get_supabase_client()
        return self._client

