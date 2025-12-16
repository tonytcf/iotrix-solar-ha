"""Config flow for Iotrix Solar integration."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .const import (
    DOMAIN,
    CONF_API_URL,
    CONF_DEVICE_ID,
    CONF_TOKEN,
    CONF_USER_AGENT,
    CONF_UPDATE_INTERVAL,
    CONF_LOGIN_API_URL,
    CONF_USERNAME,
    CONF_PASSWORD,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_USER_AGENT,
)
from .api import IotrixSolarApiClient, IotrixSolarApiError

async def validate_input(hass: HomeAssistant, data: dict) -> dict:
    """验证用户输入的参数是否有效（含API连通性测试）"""
    client = IotrixSolarApiClient(
        hass=hass,
        api_url=data[CONF_API_URL],
        device_id=data[CONF_DEVICE_ID],
        token=data[CONF_TOKEN],
        user_agent=data[CONF_USER_AGENT],
        login_api_url=data.get(CONF_LOGIN_API_URL),
        username=data.get(CONF_USERNAME),
        password=data.get(CONF_PASSWORD),
    )
    try:
        # 测试获取数据
        await client.async_get_device_data()
        return {"title": f"Iotrix Solar ({data[CONF_DEVICE_ID]})"}
    finally:
        await client.async_close()

class IotrixSolarConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """处理配置流程（支持多设备）"""

    VERSION = 1
    # 允许同一设备ID多次添加（多设备支持）
    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """处理用户初始化配置"""
        errors = {}

        if user_input is not None:
            # 可选：添加设备ID唯一校验（若需要限制同一设备只添加一次）
            # await self.async_set_unique_id(user_input[CONF_DEVICE_ID])
            # self._abort_if_unique_id_configured()
            try:
                info = await validate_input(self.hass, user_input)
                return self.async_create_entry(title=info["title"], data=user_input)
            except IotrixSolarApiError as e:
                errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "unknown"

        # 配置表单的字段定义（新增登录参数，设为可选）
        data_schema = vol.Schema(
            {
                vol.Required(CONF_API_URL): str,
                vol.Required(CONF_DEVICE_ID): str,
                vol.Required(CONF_TOKEN): str,
                vol.Optional(CONF_USER_AGENT, default=DEFAULT_USER_AGENT): str,
                vol.Optional(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): int,
                vol.Optional(CONF_LOGIN_API_URL): str,
                vol.Optional(CONF_USERNAME): str,
                vol.Optional(CONF_PASSWORD): str,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )