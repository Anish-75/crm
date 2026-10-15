from typing import Any, Dict, Optional
from app.repositories.base import BaseRepository


class ProfileRepository(BaseRepository):
    """Repository for user profiles and roles stored in the `profiles` table."""

    def get_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a profile by user UUID from Supabase."""
        response = (
            self.client.table("profiles")
            .select("*")
            .eq("id", user_id)
            .maybe_single()
            .execute()
        )
        return response.data

    def create(self, user_id: str, full_name: Optional[str] = None, role: str = "agent") -> Dict[str, Any]:
        """Insert a new profile row for a user."""
        data = {
            "id": user_id,
            "full_name": full_name,
            "role": role,
        }
        response = self.client.table("profiles").insert(data).execute()
        return response.data[0] if response.data else data

    def update(self, user_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update profile fields for a user."""
        response = (
            self.client.table("profiles")
            .update(data)
            .eq("id", user_id)
            .execute()
        )
        return response.data[0] if response.data else None

