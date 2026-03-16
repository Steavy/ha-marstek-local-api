Here's a sample Python code snippet to represent a Marstek sensor:

```python
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import ATTR_VALUE, CONF DeviceInfo
from homeassistant.helpers import entity_platform
from homeassistant.util import FMT_TIME
from homeassistant.util import async_add_entities

class MarstekSensor(SensorEntity):
    def __init__(self, coordinator: MarstekDataUpdateCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_has_entity_name = True
        device_mac = entry.data.get("ble_mac") or entry.data.get("wifi_mac")
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_mac)},
            name=f"Marstek {entry.data['device']}",
            manufacturer="Marstek",
            model=entry.data["device"],
            sw_version=str(entry.data.get("firmware", "Unknown")),
        )
        entity_description = self._attr_entry_description
        self.entity_description = entity_description

    @property
    def native_value(self) -> any:
        """Return the state of the sensor."""
        if not self.entity_description.value_fn:
            return None

        # Check if category data is fresh
        if self.entity_description.category:
            if not self.coordinator.is_category_fresh(self.entity_description.category):
                return None  # Stale data - return None instead of old value

        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def available(self) -> bool:
        """Return if entity is available - keep sensors available if we have data."""
        if self.entity_description.available_fn:
            device_data = self.coordinator.get_device_data(self._attr_device_info.device_mac)
            return self.entity_description.available_fn(device_data)
        # Keep entity available if device has any data at all (prevents "unknown" on transient failures)
        device_data = self.coordinator.get_device_data(self._attr_device_info.device_mac)
        return device_data is not None and len(device_data) > 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Marstek sensor based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]

    entities = []

    # Check if multi-device or single-device mode
    if isinstance(coordinator, MarstekMultiDeviceCoordinator):
        # Multi-device mode - create sensors for each device + aggregate sensors
        for mac in coordinator.get_device_macs():
            device_coordinator = coordinator.device_coordinators[mac]
            device_data = next(d for d in coordinator.devices if (d.get("ble_mac") or d.get("wifi_mac")) == mac)

            # Add standard sensors for this device
            for description in SENSOR_TYPES:
                entities.append(
                    MarstekSensor(coordinator=coordinator, entry=entry),
                )

            # Add PV sensors if Venus D
            if device_coordinator.device_model == DEVICE_MODEL_VENUS_D:
                for description in PV_SENSOR_TYPES:
                    entities.append(
                        MarstekSensor(coordinator=coordinator, entry=entry),
                    )

        # Add aggregate/system sensors
        # Create a synthetic unique ID for the system device
        all_macs = sorted(coordinator.get_device_macs())
        system_unique_id = "_".join(all_macs)

        for description in AGGREGATE_SENSOR_TYPES:
            entities.append(
                MarstekAggregateSensor(
                    coordinator=coordinator,
                    entity_description=description,
                    system_unique_id=system_unique_id,
                    device_count=len(all_macs),
                )
            )

    else:
        # Single device mode (legacy)
        # Add standard sensors
        for description in SENSOR_TYPES:
            entities.append(
                MarstekSensor(coordinator=coordinator, entry=entry),
            )

        # Add PV sensors if Venus D
        if coordinator.device_model == DEVICE_MODEL_VENUS_D:
            for description in PV_SENSOR_TYPES:
                entities.append(
                    MarstekSensor(coordinator=coordinator, entry=entry),
                )

    async_add_entities(entities)
```

This code snippet provides the basic structure and functionality required to implement a Marstek sensor in Home Assistant. It covers initialization, data retrieval, entity representation, and setup of sensors for multiple devices and aggregates.