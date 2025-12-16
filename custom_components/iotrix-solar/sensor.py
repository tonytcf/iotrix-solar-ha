"""Sensor platform for Iotrix Solar."""
from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN

# 传感器类型定义
SENSOR_TYPES = {
    "power": {
        "name": "Real-time Power",
        "unit": "W",
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:solar-power",
    },
    "voltage": {
        "name": "Voltage",
        "unit": "V",
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:flash",
    },
    "daily_generation": {
        "name": "Daily Generation",
        "unit": "kWh",
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "icon": "mdi:counter",
    },
    "total_generation": {
        "name": "Total Generation",
        "unit": "kWh",
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "icon": "mdi:counter",
    },
}

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """设置传感器平台"""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    entities = []
    for sensor_type in SENSOR_TYPES:
        entities.append(IotrixSolarSensor(coordinator, entry, sensor_type))
    async_add_entities(entities)

class IotrixSolarSensor(CoordinatorEntity, SensorEntity):
    """Iotrix Solar Sensor Entity"""

    def __init__(self, coordinator, entry, sensor_type):
        """初始化传感器"""
        super().__init__(coordinator)
        self._entry = entry
        self._sensor_type = sensor_type
        self._attr_name = f"Iotrix Solar {SENSOR_TYPES[sensor_type]['name']}"
        self._attr_unit_of_measurement = SENSOR_TYPES[sensor_type]["unit"]
        self._attr_state_class = SENSOR_TYPES[sensor_type]["state_class"]
        self._attr_icon = SENSOR_TYPES[sensor_type]["icon"]
        self._attr_unique_id = f"{entry.entry_id}_{sensor_type}"

    @property
    def state(self):
        """返回传感器状态"""
        return self.coordinator.data.get(self._sensor_type)