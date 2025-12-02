"""DataUpdateCoordinator for OVO Energy Australia."""

from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.event import async_track_point_in_time
from homeassistant.util import dt as dt_util

from .api import (
    OVOEnergyAUApiClient,
    OVOEnergyAUApiClientAuthenticationError,
    OVOEnergyAUApiClientCommunicationError,
    OVOEnergyAUApiClientError,
)
from .const import DOMAIN, UPDATE_HOUR, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class OVOEnergyAUDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching OVO Energy Australia data."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: OVOEnergyAUApiClient,
        account_id: str,
    ) -> None:
        """Initialize coordinator."""
        # Note: We don't set update_interval here because we schedule at a specific time (2am)
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=None,  # Disable automatic updates
        )
        self.client = client
        self.account_id = account_id
        self._unsub_refresh = None

    async def _schedule_next_refresh(self) -> None:
        """Schedule the next refresh at 2am."""
        now = dt_util.now()
        next_update = now.replace(hour=UPDATE_HOUR, minute=0, second=0, microsecond=0)

        # If 2am today has passed, schedule for tomorrow
        if next_update <= now:
            next_update += timedelta(days=1)

        _LOGGER.debug("Next automatic update scheduled for: %s", next_update)

        # Cancel existing schedule if any
        if self._unsub_refresh:
            self._unsub_refresh()

        # Schedule the update
        self._unsub_refresh = async_track_point_in_time(
            self.hass, self._async_scheduled_refresh, next_update
        )

    async def _async_scheduled_refresh(self, _now: datetime) -> None:
        """Handle scheduled refresh."""
        await self.async_request_refresh()
        # Schedule the next one
        await self._schedule_next_refresh()

    async def async_start_scheduled_updates(self) -> None:
        """Start the scheduled updates."""
        await self._schedule_next_refresh()

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API."""
        try:
            data = await self.client.get_interval_data(self.account_id)
            return self._process_data(data)
        except OVOEnergyAUApiClientAuthenticationError as err:
            raise UpdateFailed(f"Authentication error: {err}") from err
        except OVOEnergyAUApiClientCommunicationError as err:
            raise UpdateFailed(f"Communication error: {err}") from err
        except OVOEnergyAUApiClientError as err:
            raise UpdateFailed(f"API error: {err}") from err

    def _process_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Process the interval data."""
        processed = {
            "daily": {},
            "monthly": {},
            "yearly": {},
        }

        for period in ["daily", "monthly", "yearly"]:
            if period not in data:
                continue

            period_data = data[period]

            # Process solar data
            if "solar" in period_data and period_data["solar"]:
                solar_total_consumption = 0
                solar_total_charge = 0

                for entry in period_data["solar"]:
                    if entry.get("consumption"):
                        solar_total_consumption += entry["consumption"]
                    if entry.get("charge") and entry["charge"].get("value"):
                        solar_total_charge += entry["charge"]["value"]

                processed[period]["solar_consumption"] = solar_total_consumption
                processed[period]["solar_charge"] = solar_total_charge

                # Store latest entry for attributes
                if period_data["solar"]:
                    processed[period]["solar_latest"] = period_data["solar"][-1]

            # Process export data (differentiate between grid consumption and return to grid)
            if "export" in period_data and period_data["export"]:
                grid_total_consumption = 0
                grid_total_charge = 0
                return_total_consumption = 0
                return_total_charge = 0

                for entry in period_data["export"]:
                    charge_type = entry.get("charge", {}).get("type", "DEBIT")
                    consumption = entry.get("consumption", 0)
                    charge_value = entry.get("charge", {}).get("value", 0)

                    # CREDIT means returning power to grid (solar export)
                    # DEBIT, FREE, PEAK, OFF_PEAK mean consuming from grid
                    if charge_type == "CREDIT":
                        return_total_consumption += consumption
                        return_total_charge += charge_value
                    else:
                        # Default to grid consumption for DEBIT, FREE, PEAK, OFF_PEAK
                        grid_total_consumption += consumption
                        grid_total_charge += charge_value

                processed[period]["grid_consumption"] = grid_total_consumption
                processed[period]["grid_charge"] = grid_total_charge
                processed[period]["return_to_grid"] = return_total_consumption
                processed[period]["return_to_grid_charge"] = return_total_charge

                # Store latest entry for attributes
                if period_data["export"]:
                    processed[period]["grid_latest"] = period_data["export"][-1]

        return processed
