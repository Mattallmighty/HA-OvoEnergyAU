"""The OVO Energy Australia integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ACCESS_TOKEN, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import OVOEnergyAUApiClient
from .const import CONF_ACCOUNT_ID, DOMAIN
from .coordinator import OVOEnergyAUDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up OVO Energy Australia from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Create API client
    session = async_get_clientsession(hass)
    client = OVOEnergyAUApiClient(session)

    # Set tokens from config entry
    if "token" in entry.data:
        # OAuth2 flow
        client.set_tokens(
            access_token=entry.data["token"]["access_token"],
            id_token=entry.data["token"]["id_token"],
            refresh_token=entry.data["token"].get("refresh_token"),
            expires_in=entry.data["token"].get("expires_in"),
        )
    else:
        # Manual token entry
        client.set_tokens(
            access_token=entry.data[CONF_ACCESS_TOKEN],
            id_token=entry.data["id_token"],
            refresh_token=entry.data.get("refresh_token"),
        )

    # Proactively refresh token if expired before first API call
    # This prevents the "HTML instead of JSON" error during setup
    if client.token_expired and client._refresh_token:
        _LOGGER.info("Token expired, refreshing before setup")
        try:
            new_token_data = await client.refresh_tokens()

            # Update the config entry with new tokens
            new_data = dict(entry.data)
            if "token" in new_data:
                # OAuth2 flow
                new_data["token"]["access_token"] = new_token_data["access_token"]
                new_data["token"]["id_token"] = new_token_data["id_token"]
                if "refresh_token" in new_token_data:
                    new_data["token"]["refresh_token"] = new_token_data["refresh_token"]
                if "expires_in" in new_token_data:
                    new_data["token"]["expires_in"] = new_token_data["expires_in"]
            else:
                # Manual token entry
                new_data[CONF_ACCESS_TOKEN] = new_token_data["access_token"]
                new_data["id_token"] = new_token_data["id_token"]
                if "refresh_token" in new_token_data:
                    new_data["refresh_token"] = new_token_data["refresh_token"]

            hass.config_entries.async_update_entry(entry, data=new_data)
            _LOGGER.info("Token refresh successful, config entry updated")
        except Exception as err:
            _LOGGER.error("Failed to refresh expired token during setup: %s", err)
            _LOGGER.error("Please re-add the integration with fresh credentials")
            raise

    # Get account ID
    account_id = entry.data.get(CONF_ACCOUNT_ID)
    if not account_id:
        account_id = await client.get_account_id()

    # Create coordinator
    coordinator = OVOEnergyAUDataUpdateCoordinator(
        hass,
        client=client,
        account_id=account_id,
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Start scheduled updates (daily at 2am)
    await coordinator.async_start_scheduled_updates()

    # Store coordinator
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Forward entry setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services
    async def handle_refresh_data(call):
        """Handle the refresh_data service call."""
        _LOGGER.info("Manual refresh requested via service call")
        await coordinator.async_request_refresh()

    hass.services.async_register(DOMAIN, "refresh_data", handle_refresh_data)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
