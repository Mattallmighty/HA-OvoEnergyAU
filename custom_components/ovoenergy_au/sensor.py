"""Sensor platform for OVO Energy Australia."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import OVOEnergyAUDataUpdateCoordinator

from homeassistant.components.recorder.models import StatisticData, StatisticMetaData
from homeassistant.components.recorder.statistics import (
    async_import_statistics,
    get_last_statistics,
)
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)


@dataclass
class OVOEnergyAUSensorEntityDescription(SensorEntityDescription):
    """Describes OVO Energy Australia sensor entity."""

    value_fn: Callable[[dict[str, Any]], float | None] = None
    attr_fn: Callable[[dict[str, Any]], dict[str, Any]] = None


SENSOR_DESCRIPTIONS: tuple[OVOEnergyAUSensorEntityDescription, ...] = (
    # Daily sensors
    OVOEnergyAUSensorEntityDescription(
        key="daily_solar_consumption",
        name="Daily Solar Consumption",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:solar-power",
        value_fn=lambda data: data.get("daily", {}).get("solar_consumption"),
        attr_fn=lambda data: {
            "latest_entry": data.get("daily", {}).get("solar_latest"),
        },
    ),
    OVOEnergyAUSensorEntityDescription(
        key="daily_grid_consumption",
        name="Daily Grid Consumption",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:transmission-tower",
        value_fn=lambda data: data.get("daily", {}).get("grid_consumption"),
        attr_fn=lambda data: {
            "latest_entry": data.get("daily", {}).get("grid_latest"),
        },
    ),
    OVOEnergyAUSensorEntityDescription(
        key="daily_solar_charge",
        name="Daily Solar Charge",
        native_unit_of_measurement="AUD",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:currency-usd",
        value_fn=lambda data: data.get("daily", {}).get("solar_charge"),
    ),
    OVOEnergyAUSensorEntityDescription(
        key="daily_grid_charge",
        name="Daily Grid Charge",
        native_unit_of_measurement="AUD",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:currency-usd",
        value_fn=lambda data: data.get("daily", {}).get("grid_charge"),
    ),
    OVOEnergyAUSensorEntityDescription(
        key="daily_return_to_grid",
        name="Daily Return to Grid",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:transmission-tower-export",
        value_fn=lambda data: data.get("daily", {}).get("return_to_grid"),
    ),
    OVOEnergyAUSensorEntityDescription(
        key="daily_return_to_grid_charge",
        name="Daily Return to Grid Charge",
        native_unit_of_measurement="AUD",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:currency-usd",
        value_fn=lambda data: data.get("daily", {}).get("return_to_grid_charge"),
    ),
    # Monthly sensors
    OVOEnergyAUSensorEntityDescription(
        key="monthly_solar_consumption",
        name="Monthly Solar Consumption",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:solar-power",
        value_fn=lambda data: data.get("monthly", {}).get("solar_consumption"),
        attr_fn=lambda data: {
            "latest_entry": data.get("monthly", {}).get("solar_latest"),
        },
    ),
    OVOEnergyAUSensorEntityDescription(
        key="monthly_grid_consumption",
        name="Monthly Grid Consumption",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:transmission-tower",
        value_fn=lambda data: data.get("monthly", {}).get("grid_consumption"),
        attr_fn=lambda data: {
            "latest_entry": data.get("monthly", {}).get("grid_latest"),
        },
    ),
    OVOEnergyAUSensorEntityDescription(
        key="monthly_solar_charge",
        name="Monthly Solar Charge",
        native_unit_of_measurement="AUD",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:currency-usd",
        value_fn=lambda data: data.get("monthly", {}).get("solar_charge"),
    ),
    OVOEnergyAUSensorEntityDescription(
        key="monthly_grid_charge",
        name="Monthly Grid Charge",
        native_unit_of_measurement="AUD",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:currency-usd",
        value_fn=lambda data: data.get("monthly", {}).get("grid_charge"),
    ),
    OVOEnergyAUSensorEntityDescription(
        key="monthly_return_to_grid",
        name="Monthly Return to Grid",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:transmission-tower-export",
        value_fn=lambda data: data.get("monthly", {}).get("return_to_grid"),
    ),
    OVOEnergyAUSensorEntityDescription(
        key="monthly_return_to_grid_charge",
        name="Monthly Return to Grid Charge",
        native_unit_of_measurement="AUD",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:currency-usd",
        value_fn=lambda data: data.get("monthly", {}).get("return_to_grid_charge"),
    ),
    # Yearly sensors
    OVOEnergyAUSensorEntityDescription(
        key="yearly_solar_consumption",
        name="Yearly Solar Consumption",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:solar-power",
        value_fn=lambda data: data.get("yearly", {}).get("solar_consumption"),
        attr_fn=lambda data: {
            "latest_entry": data.get("yearly", {}).get("solar_latest"),
        },
    ),
    OVOEnergyAUSensorEntityDescription(
        key="yearly_grid_consumption",
        name="Yearly Grid Consumption",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:transmission-tower",
        value_fn=lambda data: data.get("yearly", {}).get("grid_consumption"),
        attr_fn=lambda data: {
            "latest_entry": data.get("yearly", {}).get("grid_latest"),
        },
    ),
    OVOEnergyAUSensorEntityDescription(
        key="yearly_solar_charge",
        name="Yearly Solar Charge",
        native_unit_of_measurement="AUD",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:currency-usd",
        value_fn=lambda data: data.get("yearly", {}).get("solar_charge"),
    ),
    OVOEnergyAUSensorEntityDescription(
        key="yearly_grid_charge",
        name="Yearly Grid Charge",
        native_unit_of_measurement="AUD",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:currency-usd",
        value_fn=lambda data: data.get("yearly", {}).get("grid_charge"),
    ),
    OVOEnergyAUSensorEntityDescription(
        key="yearly_return_to_grid",
        name="Yearly Return to Grid",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:transmission-tower-export",
        value_fn=lambda data: data.get("yearly", {}).get("return_to_grid"),
    ),
    OVOEnergyAUSensorEntityDescription(
        key="yearly_return_to_grid_charge",
        name="Yearly Return to Grid Charge",
        native_unit_of_measurement="AUD",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:currency-usd",
        value_fn=lambda data: data.get("yearly", {}).get("return_to_grid_charge"),
    ),
    # Hourly sensors (for Energy Dashboard statistics)
    OVOEnergyAUSensorEntityDescription(
        key="hourly_solar_consumption",
        name="Hourly Solar Consumption",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:solar-power",
        value_fn=lambda data: data.get("hourly", {}).get("solar_total"),
        attr_fn=lambda data: {
            "entries": data.get("hourly", {}).get("solar_entries", [])[-24:],
            "entry_count": len(data.get("hourly", {}).get("solar_entries", [])),
        },
    ),
    OVOEnergyAUSensorEntityDescription(
        key="hourly_grid_consumption",
        name="Hourly Grid Consumption",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:transmission-tower",
        value_fn=lambda data: data.get("hourly", {}).get("grid_total"),
        attr_fn=lambda data: {
            "entries": data.get("hourly", {}).get("grid_entries", [])[-24:],
            "entry_count": len(data.get("hourly", {}).get("grid_entries", [])),
        },
    ),
    OVOEnergyAUSensorEntityDescription(
        key="hourly_return_to_grid",
        name="Hourly Return to Grid",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:transmission-tower-export",
        value_fn=lambda data: data.get("hourly", {}).get("return_to_grid_total"),
        attr_fn=lambda data: {
            "entries": data.get("hourly", {}).get("return_to_grid_entries", [])[-24:],
            "entry_count": len(data.get("hourly", {}).get("return_to_grid_entries", [])),
        },
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up OVO Energy Australia sensors."""
    coordinator: OVOEnergyAUDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        OVOEnergyAUSensor(coordinator, description)
        for description in SENSOR_DESCRIPTIONS
    ]

    async_add_entities(entities)


class OVOEnergyAUSensor(CoordinatorEntity[OVOEnergyAUDataUpdateCoordinator], SensorEntity):
    """Representation of an OVO Energy Australia sensor."""

    entity_description: OVOEnergyAUSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: OVOEnergyAUDataUpdateCoordinator,
        description: OVOEnergyAUSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.account_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.account_id)},
            "name": f"OVO Energy AU {coordinator.account_id}",
            "manufacturer": "OVO Energy",
            "model": "Australia Account",
        }

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.entity_description.value_fn:
            return self.entity_description.value_fn(self.coordinator.data)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        if self.entity_description.attr_fn:
            return self.entity_description.attr_fn(self.coordinator.data)
        return {}

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        # Standard update first
        super()._handle_coordinator_update()

        # If this is an hourly sensor, attempt to import statistics
        if self.entity_description.key.startswith("hourly_"):
            self.hass.async_create_task(self._async_import_statistics())
    
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    async def _async_import_statistics(self) -> None:
        """Import hourly statistics for the Energy Dashboard."""
        if not self.coordinator.data.get("hourly"):
            _LOGGER.debug("No hourly data available in coordinator")
            return

        # Map entity keys to data keys in coordinator data
        data_key_map = {
            "hourly_solar_consumption": "solar_entries",
            "hourly_grid_consumption": "grid_entries",
            "hourly_return_to_grid": "return_to_grid_entries",
        }

        data_key = data_key_map.get(self.entity_description.key)
        if not data_key:
            return

        entries = self.coordinator.data["hourly"].get(data_key, [])
        if not entries:
            _LOGGER.debug("No entries found for %s (key: %s)", self.entity_id, data_key)
            return

        # Sort entries by time just in case
        entries.sort(key=lambda x: x["period_from"])

        statistic_id = self.entity_id
        
        # Get the last statistic to determine the running total (sum)
        # Use async_add_executor_job to avoid blocking the event loop (database I/O)
        last_stats = await self.hass.async_add_executor_job(
            get_last_statistics, self.hass, 1, statistic_id, True, {"sum"}
        )
        
        last_sum = 0.0
        if last_stats and statistic_id in last_stats and last_stats[statistic_id]:
            last_sum = last_stats[statistic_id][0].get("sum") or 0.0

        statistics = []
        current_sum = last_sum

        for entry in entries:
            try:
                # Parse timestamp (API format example: 2023-10-27T00:00:00)
                # Ensure it's timezone aware (assume local AU time or UTC? usually API gives local)
                # Note: OVO API typically returns local time. We need to handle this carefully.
                # However, for simplicity, we'll parse as is. If simplejson/string, use fromisoformat.
                
                start_time_str = entry["period_from"]
                # Assuming ISO format. If no timezone, we might need to add one.
                # dt_util.parse_datetime handles most cases.
                start_time = dt_util.parse_datetime(start_time_str)
                
                if start_time is None:
                    continue

                # Ensure timezone awareness (default to configured HA timezone if missing)
                if start_time.tzinfo is None:
                    start_time = start_time.replace(tzinfo=dt_util.get_default_time_zone())

                consumption = float(entry.get("consumption", 0.0))
                current_sum += consumption

                statistics.append(
                    StatisticData(
                        start=start_time,
                        state=consumption,
                        sum=current_sum,
                    )
                )
            except (ValueError, TypeError) as err:
                _LOGGER.error("Error processing statistic entry: %s", err)
                continue

        if statistics:
            _LOGGER.debug(
                "Importing %d statistics for %s (starting sum: %.2f)", 
                len(statistics), statistic_id, last_sum
            )
            
            metadata = StatisticMetaData(
                has_mean=False,
                has_sum=True,
                name=self.entity_description.name,
                source="recorder",  # Must be 'recorder' to import stats for this entity
                statistic_id=statistic_id,
                unit_of_measurement=self.entity_description.native_unit_of_measurement,
            )

            await async_import_statistics(self.hass, metadata, statistics)
