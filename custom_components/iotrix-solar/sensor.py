"""Sensor platform for Iotrix Solar - displays solar data (power, generation, etc.)."""
from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SENSOR_TYPES
from .helpers import slugify

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Iotrix Solar sensors from config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    # 创建所有传感器实体
    entities = []
    for sensor_type in SENSOR_TYPES:
        entities.append(IotrixSolarSensor(coordinator, entry, sensor_type))
    async_add_entities(entities)

class IotrixSolarSensor(CoordinatorEntity, SensorEntity):
    """Iotrix Solar sensor entity (power, generation, battery, etc.)."""

    def __init__(self, coordinator, entry, sensor_type):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._sensor_type = sensor_type
        self._sensor_config = SENSOR_TYPES[sensor_type]

        # 传感器基本配置
        self._attr_name = f"Iotrix Solar {self._sensor_config['name']}"
        self._attr_unit_of_measurement = self._sensor_config["unit"]
        self._attr_icon = self._sensor_config["icon"]
        self._attr_unique_id = f"{entry.entry_id}_{sensor_type}_{slugify(entry.data['device_id'])}"
        self._attr_translation_key = f"iotrix_solar_{sensor_type}"  # 翻译键

        # 状态类（符合HA能源面板规范）
        if self._sensor_config["state_class"] == "measurement":
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif self._sensor_config["state_class"] == "total_increasing":
            self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        else:
            self._attr_state_class = None

    @property
    def state(self):
        """Return the current state of the sensor."""
        return self.coordinator.data.get(self._sensor_type)

    @property
    def extra_state_attributes(self):
        """Return extra sensor attributes (for debugging)."""
        return {
            "device_id": self._entry.data["device_id"],
            "api_url": self._entry.data["api_url"],
            "integration_version": self._entry.version,
        }