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
        )

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
