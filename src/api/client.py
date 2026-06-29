import httpx
from typing import Dict, Any, Optional
from config import settings

class BaseHttpClient:
    """Base HTTP client for Claw Royale lobby REST API interactions."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.API_KEY
        
        # Normalize base_url dynamically to prevent duplicate '/api/api' path construction
        base = settings.API_URL
        if base.endswith("/api"):
            base = base[:-4]
        elif base.endswith("/api/"):
            base = base[:-5]
        self.base_url = base

    def _get_headers(self) -> Dict[str, str]:
        """Construct required REST API headers."""
        return {
            "X-API-Key": self.api_key,
            "X-Version": settings.X_VERSION,
            "Content-Type": "application/json"
        }

    async def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send HTTP GET request."""
        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=self._get_headers(), params=params)
            response.raise_for_status()
            return response.json()

    async def put(self, path: str, json_data: Optional[Dict[str, Any]] = None, headers_override: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Send HTTP PUT request."""
        url = f"{self.base_url}{path}"
        headers = headers_override if headers_override else self._get_headers()
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.put(url, headers=headers, json=json_data)
            response.raise_for_status()
            return response.json()