"""Iotrix Solar integration."""
import asyncio
import time
import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    CONF_API_URL,
    CONF_DEVICE_ID,
    CONF_TOKEN,
    CONF_USER_AGENT,
    CONF_UPDATE_INTERVAL,
)

PLATFORMS = ["sensor"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """设置集成"""
    # 初始化数据更新协调器（定时抓取数据）
    coordinator = IotrixSolarCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator}

    # 加载传感器平台
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """卸载集成"""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

class IotrixSolarCoordinator(DataUpdateCoordinator):
    """数据更新协调器"""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        """初始化协调器"""
        self.hass = hass
        self.entry = entry
        self.api_url = entry.data[CONF_API_URL]
        self.device_id = entry.data[CONF_DEVICE_ID]
        self.token = entry.data[CONF_TOKEN]
        self.user_agent = entry.data[CONF_USER_AGENT]
        update_interval = entry.data[CONF_UPDATE_INTERVAL]

        super().__init__(
            hass,
            logger=hass.logger.getChild(DOMAIN),
            name=DOMAIN,
            update_interval=asyncio.timedelta(seconds=update_interval),
        )

    async def _async_update_data(self):
        """异步抓取Iotrix数据"""
        try:
            # 使用aiohttp发送异步请求（替代requests的同步请求）
            params = {
                "deviceId": self.device_id,
                "time": int(time.time()),
            }
            headers = {
                "token": self.token,
                "User-Agent": self.user_agent,
            }
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.api_url, headers=headers, params=params, timeout=10
                ) as response:
                    if response.status != 200:
                        raise UpdateFailed(f"API请求失败：{response.status}")
                    data = await response.json()
                    # 提取数据（根据Iotrix API返回格式修改）
                    return {
                        "power": data["data"]["power"],
                        "voltage": data["data"]["voltage"],
                        "daily_generation": data["data"]["dailyGen"],
                        "total_generation": data["data"]["totalGen"],
                    }
        except Exception as e:
            raise UpdateFailed(f"抓取数据失败：{str(e)}") from e