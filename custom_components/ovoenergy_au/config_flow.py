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
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_PASSWORD, CONF_USERNAME
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
        # Always use username/password authentication
        return await self.async_step_auth(user_input)

    async def async_step_auth(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle username/password authentication."""
        errors = {}

        if user_input is not None:
            try:
                session = async_get_clientsession(self.hass)
                client = OVOEnergyAUApiClient(session)

                # Authenticate with username/password
                _LOGGER.info("Attempting authentication for user: %s", user_input[CONF_USERNAME])
                token_data = await client.authenticate_with_password(
                    username=user_input[CONF_USERNAME],
                    password=user_input[CONF_PASSWORD],
                )

                # Get account ID
                account_id = await client.get_account_id()

                # Test connection
                if await client.test_connection(account_id):
                    return self.async_create_entry(
                        title=f"OVO Energy AU ({account_id})",
                        data={
                            CONF_ACCESS_TOKEN: token_data["access_token"],
                            "id_token": token_data["id_token"],
                            "refresh_token": token_data.get("refresh_token"),
                            CONF_ACCOUNT_ID: account_id,
                            CONF_USERNAME: user_input[CONF_USERNAME],
                            CONF_PASSWORD: user_input[CONF_PASSWORD],
                        },
                    )
                errors["base"] = ERROR_CANNOT_CONNECT
            except OVOEnergyAUApiClientAuthenticationError as err:
                _LOGGER.error("Authentication failed: %s", err)
                errors["base"] = ERROR_AUTH_FAILED
            except OVOEnergyAUApiClientCommunicationError as err:
                _LOGGER.error("Communication error: %s", err)
                errors["base"] = ERROR_CANNOT_CONNECT
            except Exception as err:
                _LOGGER.exception("Unexpected exception: %s", err)
                errors["base"] = ERROR_UNKNOWN

        # Show form for username/password entry
        return self.async_show_form(
            step_id="auth",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "docs_url": "https://github.com/Mattallmighty/HA-OvoEnergyAU",
            },
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> FlowResult:
        """Handle re-authentication."""
        self.entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm re-authentication."""
        errors = {}

        if user_input is not None:
            try:
                session = async_get_clientsession(self.hass)
                client = OVOEnergyAUApiClient(session)

                # Authenticate with username/password
                username = user_input[CONF_USERNAME]
                password = user_input[CONF_PASSWORD]

                token_data = await client.authenticate_with_password(username, password)

                # Update existing entry
                new_data = dict(self.entry.data)
                
                # Update tokens
                if "token" in new_data:
                    # If previously using OAuth2 structure
                    new_data["token"]["access_token"] = token_data["access_token"]
                    new_data["token"]["id_token"] = token_data["id_token"]
                    new_data["token"]["refresh_token"] = token_data.get("refresh_token")
                    new_data["token"]["expires_in"] = token_data.get("expires_in")
                else:
                    # Manual/Flat structure
                    new_data[CONF_ACCESS_TOKEN] = token_data["access_token"]
                    new_data["id_token"] = token_data["id_token"]
                    new_data["refresh_token"] = token_data.get("refresh_token")
                
                # Ensure username is saved if it wasn't before
                new_data[CONF_USERNAME] = username
                new_data[CONF_PASSWORD] = password

                self.hass.config_entries.async_update_entry(
                    self.entry,
                    data=new_data
                )

                self.hass.config_entries.async_reload(self.entry.entry_id)
                return self.async_abort(reason="reauth_successful")

            except OVOEnergyAUApiClientAuthenticationError:
                errors["base"] = ERROR_AUTH_FAILED
            except Exception as err:
                _LOGGER.exception("Reauthentication error: %s", err)
                errors["base"] = ERROR_UNKNOWN

        # Default username to existing one if available
        default_username = (
            self.entry.data.get(CONF_USERNAME) 
            if hasattr(self, "entry") and self.entry and CONF_USERNAME in self.entry.data 
            else ""
        )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME, default=default_username): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
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
