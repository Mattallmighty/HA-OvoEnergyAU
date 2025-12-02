"""Config flow for OVO Energy Australia integration."""

from __future__ import annotations

import base64
import hashlib
import logging
import secrets
from typing import Any
from urllib.parse import urlencode

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_ACCESS_TOKEN
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    OVOEnergyAUApiClient,
    OVOEnergyAUApiClientAuthenticationError,
    OVOEnergyAUApiClientCommunicationError,
    OVOEnergyAUApiClientError,
)
from .const import (
    CONF_ACCOUNT_ID,
    DOMAIN,
    ERROR_AUTH_FAILED,
    ERROR_CANNOT_CONNECT,
    ERROR_UNKNOWN,
    OAUTH_AUDIENCE,
    OAUTH_AUTHORIZE_URL,
    OAUTH_CLIENT_ID,
    OAUTH_SCOPES,
    OAUTH_TOKEN_URL,
)

_LOGGER = logging.getLogger(__name__)


class OVOEnergyAUOAuth2FlowHandler(config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN):
    """Handle OVO Energy Australia OAuth2 flow."""

    DOMAIN = DOMAIN

    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return _LOGGER

    @property
    def extra_authorize_data(self) -> dict[str, Any]:
        """Extra data that needs to be appended to the authorize url."""
        # Generate PKCE parameters
        code_verifier = base64.urlsafe_b64encode(
            secrets.token_bytes(32)
        ).decode('utf-8').rstrip('=')
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode('utf-8')).digest()
        ).decode('utf-8').rstrip('=')

        # Store code_verifier for later use in token exchange
        self.flow_impl.code_verifier = code_verifier

        return {
            "audience": OAUTH_AUDIENCE,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initialized by the user."""
        return await self.async_step_pick_implementation()

    async def async_oauth_create_entry(self, data: dict[str, Any]) -> FlowResult:
        """Create an entry for OVO Energy Australia."""
        session = async_get_clientsession(self.hass)
        client = OVOEnergyAUApiClient(session)

        # Set tokens from OAuth2 data
        client.set_tokens(
            access_token=data["token"]["access_token"],
            id_token=data["token"]["id_token"],
            refresh_token=data["token"].get("refresh_token"),
            expires_in=data["token"].get("expires_in"),
        )

        try:
            # Get account ID from token
            account_id = await client.get_account_id()

            # Test the connection
            if not await client.test_connection(account_id):
                return self.async_abort(reason=ERROR_CANNOT_CONNECT)

            # Create the entry
            return self.async_create_entry(
                title=f"OVO Energy AU ({account_id})",
                data={
                    **data,
                    CONF_ACCOUNT_ID: account_id,
                },
            )
        except OVOEnergyAUApiClientAuthenticationError:
            return self.async_abort(reason=ERROR_AUTH_FAILED)
        except OVOEnergyAUApiClientCommunicationError:
            return self.async_abort(reason=ERROR_CANNOT_CONNECT)
        except Exception as err:
            _LOGGER.exception("Unexpected error: %s", err)
            return self.async_abort(reason=ERROR_UNKNOWN)


class OVOEnergyAUFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle OVO Energy Australia config flow (fallback if OAuth2 not available)."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initialized by the user."""
        # Check if OAuth2 is configured
        if not self.hass.data.get("auth_implementations", {}).get(DOMAIN):
            # OAuth2 not configured, show manual token entry
            return await self.async_step_manual_tokens(user_input)

        # OAuth2 is configured, use it
        return await self.async_step_pick_implementation(user_input)

    async def async_step_manual_tokens(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle manual token entry."""
        errors = {}

        if user_input is not None:
            try:
                session = async_get_clientsession(self.hass)
                client = OVOEnergyAUApiClient(session)

                # Set tokens
                client.set_tokens(
                    access_token=user_input[CONF_ACCESS_TOKEN],
                    id_token=user_input["id_token"],
                )

                # Get account ID
                account_id = await client.get_account_id()

                # Test connection
                if await client.test_connection(account_id):
                    return self.async_create_entry(
                        title=f"OVO Energy AU ({account_id})",
                        data={
                            CONF_ACCESS_TOKEN: user_input[CONF_ACCESS_TOKEN],
                            "id_token": user_input["id_token"],
                            CONF_ACCOUNT_ID: account_id,
                        },
                    )
                errors["base"] = ERROR_CANNOT_CONNECT
            except OVOEnergyAUApiClientAuthenticationError:
                errors["base"] = ERROR_AUTH_FAILED
            except OVOEnergyAUApiClientCommunicationError:
                errors["base"] = ERROR_CANNOT_CONNECT
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = ERROR_UNKNOWN

        # Show form for manual token entry
        return self.async_show_form(
            step_id="manual_tokens",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ACCESS_TOKEN): str,
                    vol.Required("id_token"): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "docs_url": "https://github.com/Mattallmighty/HA-OvoEnergyAU",
            },
        )


async def async_get_config_entry_implementation(
    hass: HomeAssistant,
) -> config_entry_oauth2_flow.AbstractOAuth2Implementation:
    """Return OAuth2 implementation for this integration."""
    return OVOEnergyAUOAuth2Implementation(hass)


class OVOEnergyAUOAuth2Implementation(config_entry_oauth2_flow.AbstractOAuth2Implementation):
    """OVO Energy Australia OAuth2 implementation."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize OVO Energy AU OAuth2 implementation."""
        self.hass = hass
        self.code_verifier: str | None = None

    @property
    def name(self) -> str:
        """Name of the implementation."""
        return "OVO Energy Australia"

    @property
    def domain(self) -> str:
        """Domain of the implementation."""
        return DOMAIN

    @property
    def redirect_uri(self) -> str:
        """Return the redirect uri."""
        return f"{self.hass.config.external_url}/auth/external/callback"

    async def async_generate_authorize_url(self, flow_id: str) -> str:
        """Generate authorization URL."""
        params = {
            "client_id": OAUTH_CLIENT_ID,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(OAUTH_SCOPES),
            "state": flow_id,
        }

        return f"{OAUTH_AUTHORIZE_URL}?{urlencode(params)}"

    async def async_resolve_external_data(self, external_data: Any) -> dict[str, Any]:
        """Resolve external data to tokens."""
        # Exchange code for tokens
        session = async_get_clientsession(self.hass)

        data = {
            "grant_type": "authorization_code",
            "client_id": OAUTH_CLIENT_ID,
            "code": external_data["code"],
            "redirect_uri": self.redirect_uri,
            "code_verifier": self.code_verifier,
        }

        async with session.post(OAUTH_TOKEN_URL, json=data) as response:
            response.raise_for_status()
            token_data = await response.json()

        return {
            "token": token_data,
        }

    async def _async_refresh_token(self, token: dict[str, Any]) -> dict[str, Any]:
        """Refresh a token."""
        session = async_get_clientsession(self.hass)

        data = {
            "grant_type": "refresh_token",
            "client_id": OAUTH_CLIENT_ID,
            "refresh_token": token["refresh_token"],
        }

        async with session.post(OAUTH_TOKEN_URL, json=data) as response:
            response.raise_for_status()
            token_data = await response.json()

        return {
            "token": token_data,
        }
