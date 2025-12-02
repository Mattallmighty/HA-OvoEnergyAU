"""API client for OVO Energy Australia."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
import logging
from typing import Any

import aiohttp
import jwt

from .const import (
    API_BASE_URL,
    AUTH_BASE_URL,
    GET_CONTACT_INFO_QUERY,
    GET_INTERVAL_DATA_QUERY,
    GRAPHQL_URL,
    OAUTH_AUDIENCE,
    OAUTH_CLIENT_ID,
    OAUTH_SCOPES,
    OAUTH_TOKEN_URL,
)

_LOGGER = logging.getLogger(__name__)


class OVOEnergyAUApiClientError(Exception):
    """Exception to indicate a general API error."""


class OVOEnergyAUApiClientAuthenticationError(OVOEnergyAUApiClientError):
    """Exception to indicate an authentication error."""


class OVOEnergyAUApiClientCommunicationError(OVOEnergyAUApiClientError):
    """Exception to indicate a communication error."""


class OVOEnergyAUApiClient:
    """API client for OVO Energy Australia."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
    ) -> None:
        """Initialize the API client."""
        self._session = session
        self._access_token: str | None = None
        self._id_token: str | None = None
        self._refresh_token: str | None = None
        self._token_expires_at: datetime | None = None

    @property
    def is_authenticated(self) -> bool:
        """Return True if the client is authenticated."""
        return self._access_token is not None and not self.token_expired

    @property
    def token_expired(self) -> bool:
        """Return True if the token has expired."""
        if self._token_expires_at is None:
            return True
        # Add 5 minute buffer
        return datetime.now() >= (self._token_expires_at - timedelta(minutes=5))

    def set_tokens(
        self,
        access_token: str,
        id_token: str,
        refresh_token: str | None = None,
        expires_in: int | None = None,
    ) -> None:
        """Set authentication tokens."""
        self._access_token = access_token
        self._id_token = id_token
        self._refresh_token = refresh_token

        if expires_in:
            self._token_expires_at = datetime.now() + timedelta(seconds=expires_in)
        else:
            # Try to decode the JWT to get expiration
            try:
                decoded = jwt.decode(
                    access_token,
                    options={"verify_signature": False},
                )
                exp_timestamp = decoded.get("exp")
                if exp_timestamp:
                    self._token_expires_at = datetime.fromtimestamp(exp_timestamp)
                else:
                    # Default to 1 hour
                    self._token_expires_at = datetime.now() + timedelta(hours=1)
            except Exception:
                # Default to 1 hour
                self._token_expires_at = datetime.now() + timedelta(hours=1)

        _LOGGER.debug("Tokens set, expires at: %s", self._token_expires_at)

    async def exchange_code_for_tokens(
        self,
        code: str,
        redirect_uri: str,
        code_verifier: str,
    ) -> dict[str, Any]:
        """Exchange authorization code for tokens."""
        data = {
            "grant_type": "authorization_code",
            "client_id": OAUTH_CLIENT_ID,
            "code": code,
            "redirect_uri": redirect_uri,
            "code_verifier": code_verifier,
        }

        try:
            async with self._session.post(OAUTH_TOKEN_URL, json=data) as response:
                response.raise_for_status()
                token_data = await response.json()

                self.set_tokens(
                    access_token=token_data["access_token"],
                    id_token=token_data["id_token"],
                    refresh_token=token_data.get("refresh_token"),
                    expires_in=token_data.get("expires_in"),
                )

                return token_data
        except aiohttp.ClientError as err:
            raise OVOEnergyAUApiClientCommunicationError(
                "Error communicating with Auth0"
            ) from err
        except Exception as err:
            raise OVOEnergyAUApiClientAuthenticationError(
                "Error exchanging code for tokens"
            ) from err

    async def refresh_tokens(self) -> dict[str, Any]:
        """Refresh access token using refresh token."""
        if not self._refresh_token:
            raise OVOEnergyAUApiClientAuthenticationError("No refresh token available")

        data = {
            "grant_type": "refresh_token",
            "client_id": OAUTH_CLIENT_ID,
            "refresh_token": self._refresh_token,
        }

        try:
            async with self._session.post(OAUTH_TOKEN_URL, json=data) as response:
                response.raise_for_status()
                token_data = await response.json()

                self.set_tokens(
                    access_token=token_data["access_token"],
                    id_token=token_data["id_token"],
                    refresh_token=token_data.get("refresh_token", self._refresh_token),
                    expires_in=token_data.get("expires_in"),
                )

                return token_data
        except aiohttp.ClientError as err:
            raise OVOEnergyAUApiClientCommunicationError(
                "Error refreshing tokens"
            ) from err
        except Exception as err:
            raise OVOEnergyAUApiClientAuthenticationError(
                "Error refreshing tokens"
            ) from err

    async def _ensure_authenticated(self) -> None:
        """Ensure the client is authenticated."""
        if not self._access_token:
            raise OVOEnergyAUApiClientAuthenticationError("Not authenticated")

        if self.token_expired and self._refresh_token:
            _LOGGER.debug("Token expired, refreshing...")
            await self.refresh_tokens()
            _LOGGER.debug("Token refreshed successfully")

    async def get_contact_info(self) -> dict[str, Any]:
        """Get contact information and account details."""
        await self._ensure_authenticated()

        # Extract email from ID token
        try:
            decoded_id = jwt.decode(
                self._id_token,
                options={"verify_signature": False},
            )
            email = decoded_id.get('email')
            if not email:
                raise OVOEnergyAUApiClientError("Email not found in ID token")
        except Exception as err:
            raise OVOEnergyAUApiClientError(
                f"Error decoding ID token: {err}"
            ) from err

        headers = {
            "accept": "*/*",
            "authorization": f"Bearer {self._access_token}",
            "content-type": "application/json",
            "myovo-id-token": self._id_token,
            "origin": API_BASE_URL,
            "referer": f"{API_BASE_URL}/",
        }

        payload = {
            "operationName": "GetContactInfo",
            "variables": {
                "input": {
                    "email": email
                }
            },
            "query": GET_CONTACT_INFO_QUERY
        }

        try:
            async with self._session.post(
                GRAPHQL_URL,
                json=payload,
                headers=headers,
            ) as response:
                response.raise_for_status()
                data = await response.json()

                if "errors" in data:
                    error_messages = [error.get("message", "Unknown error") for error in data["errors"]]
                    raise OVOEnergyAUApiClientError(f"GraphQL errors: {', '.join(error_messages)}")

                if "data" not in data or "GetContactInfo" not in data["data"]:
                    raise OVOEnergyAUApiClientError("Invalid response from API")

                return data["data"]["GetContactInfo"]
        except aiohttp.ClientResponseError as err:
            if err.status == 401:
                raise OVOEnergyAUApiClientAuthenticationError(
                    "Authentication failed"
                ) from err
            raise OVOEnergyAUApiClientCommunicationError(
                f"Error communicating with API: {err}"
            ) from err
        except aiohttp.ClientError as err:
            raise OVOEnergyAUApiClientCommunicationError(
                f"Error communicating with API: {err}"
            ) from err

    async def get_account_ids(self) -> list[str]:
        """Get all account IDs for the user."""
        contact_info = await self.get_contact_info()
        accounts = contact_info.get("accounts", [])

        # Filter for active (non-closed) accounts
        active_accounts = [a for a in accounts if not a.get("closed", False)]

        if not active_accounts:
            raise OVOEnergyAUApiClientError("No active accounts found")

        return [str(account["id"]) for account in active_accounts]

    async def get_account_id(self) -> str:
        """Get the primary (first) active account ID."""
        account_ids = await self.get_account_ids()
        if not account_ids:
            raise OVOEnergyAUApiClientError("No account IDs found")
        return account_ids[0]

    async def get_interval_data(self, account_id: str) -> dict[str, Any]:
        """Get interval data for an account."""
        await self._ensure_authenticated()

        headers = {
            "accept": "*/*",
            "authorization": f"Bearer {self._access_token}",
            "content-type": "application/json",
            "myovo-id-token": self._id_token,
            "origin": API_BASE_URL,
            "referer": f"{API_BASE_URL}/usage",
        }

        payload = {
            "operationName": "GetIntervalData",
            "variables": {
                "input": {
                    "accountId": account_id
                }
            },
            "query": GET_INTERVAL_DATA_QUERY
        }

        try:
            async with self._session.post(
                GRAPHQL_URL,
                json=payload,
                headers=headers,
            ) as response:
                response.raise_for_status()
                data = await response.json()

                if "errors" in data:
                    error_messages = [error.get("message", "Unknown error") for error in data["errors"]]
                    raise OVOEnergyAUApiClientError(f"GraphQL errors: {', '.join(error_messages)}")

                if "data" not in data:
                    raise OVOEnergyAUApiClientError("Invalid response from API")

                return data["data"]["GetIntervalData"]
        except aiohttp.ClientResponseError as err:
            if err.status == 401:
                raise OVOEnergyAUApiClientAuthenticationError(
                    "Authentication failed"
                ) from err
            raise OVOEnergyAUApiClientCommunicationError(
                f"Error communicating with API: {err}"
            ) from err
        except aiohttp.ClientError as err:
            raise OVOEnergyAUApiClientCommunicationError(
                f"Error communicating with API: {err}"
            ) from err

    async def test_connection(self, account_id: str) -> bool:
        """Test the connection to the API."""
        try:
            await self.get_interval_data(account_id)
            return True
        except Exception as err:
            _LOGGER.error("Connection test failed: %s", err)
            return False
