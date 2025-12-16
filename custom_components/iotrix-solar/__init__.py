"""Iotrix Solar integration."""
import asyncio
import time
from typing import Dict, Any
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.helpers.storage import Store
from homeassistant.util import slugify

from .const import (
    DOMAIN,
    PLATFORMS,
    CONF_API_URL,
    CONF_DEVICE_ID,
    CONF_TOKEN,
    CONF_USER_AGENT,
    CONF_UPDATE_INTERVAL,
    CONF_LOGIN_API_URL,
    CONF_USERNAME,
    CONF_PASSWORD,
    CACHE_KEY,
)
from .api import IotrixSolarApiClient, IotrixSolarApiError, IotrixSolarAuthError

# 缓存存储版本（用于数据迁移）
STORAGE_VERSION = 1
# 缓存文件过期时间（7天）
STORAGE_EXPIRE = 60 * 60 * 24 * 7

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """设置集成（支持多设备）"""
    # 初始化API客户端
    client = IotrixSolarApiClient(
        hass=hass,
        api_url=entry.data[CONF_API_URL],
        device_id=entry.data[CONF_DEVICE_ID],
        token=entry.data[CONF_TOKEN],
        user_agent=entry.data[CONF_USER_AGENT],
        login_api_url=entry.data.get(CONF_LOGIN_API_URL),
        username=entry.data.get(CONF_USERNAME),
        password=entry.data.get(CONF_PASSWORD),
    )
    # 初始化数据缓存
    store = Store(hass, STORAGE_VERSION, f"{DOMAIN}_{slugify(entry.entry_id)}_cache")
    cached_data = await store.async_load() or {}

    # 初始化数据更新协调器
    async def async_update_data() -> Dict[str, Any]:
        """异步抓取Iotrix数据（含缓存和token刷新）"""
        try:
            data = await client.async_get_device_data()
            # 保存缓存
            cached_data.update(data)
            await store.async_save(cached_data)
            hass.logger.debug(f"[{entry.data[CONF_DEVICE_ID]}] 成功获取数据：{data}")
            return data
        except IotrixSolarAuthError as e:
            hass.logger.error(f"[{entry.data[CONF_DEVICE_ID]}] 认证失败：{e}")
            # 认证失败时返回缓存数据（若有）
            if cached_data:
                return cached_data
            raise UpdateFailed(f"认证失败且无缓存数据：{e}") from e
        except IotrixSolarApiError as e:
            hass.logger.warning(f"[{entry.data[CONF_DEVICE_ID]}] 获取数据失败：{e}")
            # API失败时返回缓存数据（若有）
            if cached_data:
                return cached_data
            raise UpdateFailed(f"获取数据失败且无缓存数据：{e}") from e

    coordinator = DataUpdateCoordinator(
        hass,
        logger=hass.logger.getChild(DOMAIN),
        name=f"{DOMAIN}_{entry.data[CONF_DEVICE_ID]}",
        update_method=async_update_data,
        update_interval=asyncio.timedelta(seconds=entry.data[CONF_UPDATE_INTERVAL]),
    )

    # 首次刷新数据
    await coordinator.async_config_entry_first_refresh()

    # 存储数据到hass上下文
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
        "store": store,
    }

    # 加载传感器平台
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # 监听配置更新
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """卸载集成（关闭API会话）"""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        # 关闭API会话
        client = hass.data[DOMAIN][entry.entry_id]["client"]
        await client.async_close()
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """更新集成配置（如修改更新间隔）"""
    await hass.config_entries.async_reload(entry.entry_id)