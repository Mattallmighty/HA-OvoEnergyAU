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
