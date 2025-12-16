"""Iotrix Solar integration - main entry point."""
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
import asyncio

from .const import DOMAIN, PLATFORMS, CONF_UPDATE_INTERVAL
from .api import (
    IotrixSolarApiClient,
    IotrixSolarApiError,
    IotrixSolarAuthError,
)

# 初始化集成（由HA自动调用）
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Iotrix Solar from a config entry."""
    # 初始化API客户端
    client = IotrixSolarApiClient(
        hass=hass,
        api_url=entry.data[CONF_API_URL],
        device_id=entry.data[CONF_DEVICE_ID],
        token=entry.data.get(CONF_TOKEN),
        cookie=entry.data.get(CONF_COOKIE),
        update_interval=entry.data[CONF_UPDATE_INTERVAL],
        qrcode_api_url=entry.data.get(CONF_QRCODE_API_URL),
        qrcode_status_api_url=entry.data.get(CONF_QRCODE_STATUS_API_URL),
        token_api_url=entry.data.get(CONF_TOKEN_API_URL),
    )

    # 定义数据更新方法（核心：定期获取设备数据）
    async def async_update_data():
        """Fetch new data from Iotrix API."""
        try:
            return await client.async_get_device_data()
        except IotrixSolarAuthError as e:
            # Token/Cookie失效，标记状态并抛出异常
            return {
                "pv_power": 0.0,
                "daily_generation": 0.0,
                "total_generation": 0.0,
                "battery_soc": 0.0,
                "token_status": "expired",
            }
        except IotrixSolarApiError as e:
            raise UpdateFailed(f"Failed to fetch data: {str(e)}") from e

    # 初始化数据协调器（定期更新数据）
    coordinator = DataUpdateCoordinator(
        hass,
        hass.logger.getChild(DOMAIN),
        name=f"Iotrix Solar ({entry.data['device_id']})",
        update_method=async_update_data,
        update_interval=asyncio.timedelta(seconds=entry.data[CONF_UPDATE_INTERVAL]),
    )

    # 首次刷新数据
    await coordinator.async_config_entry_first_refresh()

    # 存储客户端和协调器到HA上下文
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
    }

    # 加载传感器和摄像头平台
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # 监听配置更新（如用户修改参数后重新加载）
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Iotrix Solar config entry (clean up resources)."""
    # 卸载平台
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        # 关闭API会话
        client = hass.data[DOMAIN][entry.entry_id]["client"]
        await client.async_close()
        # 移除上下文数据
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update config entry options (reload integration)."""
    await hass.config_entries.async_reload(entry.entry_id)