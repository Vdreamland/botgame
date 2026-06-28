# -*- coding: utf-8 -*-
"""
ClawRoyale REST API Client.
Manages HTTP connection logic, retries, and document caching.
"""

import httpx
import asyncio
from typing import Dict, Any, Optional

from utils.logger import AgentLogger
from utils.rate_limiter import TokenBucket
from core.network.document_cache import DocumentCacheManager

class APIClientError(Exception):
    pass

class APIClient:
    def __init__(self, agent_name: str, api_key: str, base_url: str, rest_limiter: TokenBucket):
        self.agent_name = agent_name
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.rest_limiter = rest_limiter
        
        self.logger = AgentLogger.get_logger(agent_name)
        self.cache = DocumentCacheManager()
        self.client = httpx.AsyncClient(timeout=15.0)

    async def close(self) -> None:
        await self.client.aclose()

    def _get_headers(self, additional_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "X-Version": "1.11.2",
            "Authorization": f"mr-auth {self.api_key}"
        }
        if additional_headers:
            headers.update(additional_headers)
        return headers

    async def safe_request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None, 
                           headers_override: Optional[Dict[str, str]] = None, retries: int = 3) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self._get_headers(headers_override)
        
        for attempt in range(1, retries + 1):
            await self.rest_limiter.consume(1.0)
            try:
                response = await self.client.request(
                    method=method,
                    url=url,
                    json=data if data else None,
                    headers=headers
                )
                
                if response.status_code == 429:
                    self.logger.warning(f"REST Rate limited (429) on attempt {attempt}/{retries}. Backing off...")
                    await asyncio.sleep(2.0 * attempt)
                    continue
                    
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as hse:
                self.logger.error(f"HTTP Error on {method} {endpoint}: Status {hse.response.status_code}")
                if hse.response.status_code in [500, 502, 503, 504] and attempt < retries:
                    await asyncio.sleep(1.0 * attempt)
                    continue
                raise APIClientError(f"API Error {hse.response.status_code}: {hse.response.text}")
                
            except httpx.RequestError as re:
                self.logger.error(f"Network error on {method} {endpoint}: {str(re)}")
                if attempt < retries:
                    await asyncio.sleep(1.0 * attempt)
                    continue
                raise APIClientError(f"REST connection failed after {retries} attempts.")
        
        raise APIClientError("HTTP request failed consistently.")

    async def get_account_me(self) -> Dict[str, Any]:
        return await self.safe_request("GET", "accounts/me")

    async def claim_welcome_pack(self) -> Dict[str, Any]:
        # Koreksi endpoint agar mengarah ke 'redeem' (tanpa duplikasi kata 'api') [3]
        return await self.safe_request("POST", "redeem", data={"code": "WELCOME"})

    async def fetch_cached_document(self, document_path: str) -> str:
        url = f"{self.base_url}/{document_path.lstrip('/')}"
        cached_etag = self.cache.get_etag(document_path)
        
        headers = self._get_headers()
        if cached_etag:
            headers["If-None-Match"] = cached_etag
            
        await self.rest_limiter.consume(1.0)
        try:
            response = await self.client.get(url, headers=headers)
            
            if response.status_code == 304:
                self.logger.info(f"Document '{document_path}' unmodified. Using local cache.")
                cached_content = self.cache.read_cache(document_path)
                if cached_content is not None:
                    return cached_content
                return await self.fetch_cached_document(document_path)
                
            response.raise_for_status()
            
            etag = response.headers.get("ETag", "").strip('"')
            content = response.text
            
            if etag:
                self.cache.update_cache(document_path, etag, content)
                self.logger.info(f"Document '{document_path}' cache refreshed.")
            return content
            
        except Exception as e:
            self.logger.error(f"Failed to fetch document {document_path}: {str(e)}")
            cached_content = self.cache.read_cache(document_path)
            if cached_content is not None:
                return cached_content
            raise APIClientError(f"No local cache for document '{document_path}'")