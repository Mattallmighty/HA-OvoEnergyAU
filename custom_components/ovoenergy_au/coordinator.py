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
from .const import DOMAIN, UPDATE_HOUR, UPDATE_INTERVAL, HOURLY_DATA_DAYS

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
            # Fetch interval data (daily/monthly/yearly)
            interval_data = await self.client.get_interval_data(self.account_id)
            processed_data = self._process_data(interval_data)

            # Fetch hourly data for the last N days
            now = dt_util.now()
            end_date = now.strftime("%Y-%m-%d")
            start_date = (now - timedelta(days=HOURLY_DATA_DAYS)).strftime("%Y-%m-%d")

            try:
                hourly_data = await self.client.get_hourly_data(
                    self.account_id,
                    start_date,
                    end_date,
                )
                processed_data["hourly"] = self._process_hourly_data(hourly_data)
                _LOGGER.debug("Successfully fetched hourly data from %s to %s", start_date, end_date)
            except Exception as err:
                _LOGGER.warning("Failed to fetch hourly data: %s", err)
                processed_data["hourly"] = {}

            return processed_data
        except OVOEnergyAUApiClientAuthenticationError as err:
            raise UpdateFailed(f"Authentication error: {err}") from err
        except OVOEnergyAUApiClientCommunicationError as err:
            raise UpdateFailed(f"Communication error: {err}") from err
        except OVOEnergyAUApiClientError as err:
            raise UpdateFailed(f"API error: {err}") from err

    def _process_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Process the interval data.

        Note: The API returns arrays of historical data:
        - daily: array of individual day entries (latest = most recent day)
        - monthly: array of individual month entries (latest = current month)
        - yearly: array of individual year entries (latest = current year)

        We only use the LATEST entry from each array.
        """
        processed = {
            "daily": {},
            "monthly": {},
            "yearly": {},
        }

        for period in ["daily", "monthly", "yearly"]:
            if period not in data:
                continue

            period_data = data[period]

            # Process solar data - use only the LATEST entry
            if "solar" in period_data and period_data["solar"]:
                # Get the most recent entry (last in array)
                latest_solar = period_data["solar"][-1]

                processed[period]["solar_consumption"] = latest_solar.get("consumption", 0)
                processed[period]["solar_charge"] = latest_solar.get("charge", {}).get("value", 0)
                processed[period]["solar_latest"] = latest_solar

            # Process export data - use only the LATEST entry
            # (differentiate between grid consumption and return to grid based on charge type)
            if "export" in period_data and period_data["export"]:
                # Get the most recent entry (last in array)
                latest_export = period_data["export"][-1]

                charge_type = latest_export.get("charge", {}).get("type", "DEBIT")
                consumption = latest_export.get("consumption", 0)
                charge_value = latest_export.get("charge", {}).get("value", 0)

                # CREDIT means returning power to grid (solar export)
                # DEBIT, FREE, PEAK, OFF_PEAK mean consuming from grid
                if charge_type == "CREDIT":
                    processed[period]["grid_consumption"] = 0
                    processed[period]["grid_charge"] = 0
                    processed[period]["return_to_grid"] = consumption
                    processed[period]["return_to_grid_charge"] = charge_value
                else:
                    # Default to grid consumption for DEBIT, FREE, PEAK, OFF_PEAK
                    processed[period]["grid_consumption"] = consumption
                    processed[period]["grid_charge"] = charge_value
                    processed[period]["return_to_grid"] = 0
                    processed[period]["return_to_grid_charge"] = 0

                processed[period]["grid_latest"] = latest_export

        return processed

    def _process_hourly_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Process hourly data.

        Note: Unlike interval data, we keep ALL hourly entries for graphing.
        This allows Home Assistant to display hourly consumption graphs.
        """
        processed = {
            "solar_entries": [],
            "grid_entries": [],
            "return_to_grid_entries": [],
            "solar_total": 0,
            "grid_total": 0,
            "return_to_grid_total": 0,
        }

        # Process solar data - keep all entries
        if "solar" in data and data["solar"]:
            solar_entries = data["solar"]
            for entry in solar_entries:
                processed["solar_entries"].append({
                    "period_from": entry.get("periodFrom"),
                    "period_to": entry.get("periodTo"),
                    "consumption": entry.get("consumption", 0),
                    "charge": entry.get("charge", {}).get("value", 0),
                    "charge_type": entry.get("charge", {}).get("type"),
                })
                processed["solar_total"] += entry.get("consumption", 0)

        # Process export data - separate into grid consumption and return to grid
        if "export" in data and data["export"]:
            export_entries = data["export"]
            for entry in export_entries:
                consumption = entry.get("consumption", 0)
                charge_data = entry.get("charge") or {}
                charge_value = charge_data.get("value", 0)
                charge_type = charge_data.get("type", "DEBIT")

                entry_data = {
                    "period_from": entry.get("periodFrom"),
                    "period_to": entry.get("periodTo"),
                    "consumption": consumption,
                    "charge": charge_value,
                    "charge_type": charge_type,
                }

                # CREDIT means returning power to grid (solar export)
                # DEBIT, FREE, PEAK, OFF_PEAK mean consuming from grid
                if charge_type == "CREDIT":
                    processed["return_to_grid_entries"].append(entry_data)
                    processed["return_to_grid_total"] += consumption
                else:
                    processed["grid_entries"].append(entry_data)
                    processed["grid_total"] += consumption

        return processed
