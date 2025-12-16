"""Config flow for Iotrix Solar integration."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONF_API_URL,
    CONF_DEVICE_ID,
    CONF_TOKEN,
    CONF_USER_AGENT,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_USER_AGENT,
)

async def validate_input(hass: HomeAssistant, data: dict) -> dict:
    """验证用户输入的参数是否有效（可添加API连通性测试）"""
    # 这里可添加异步请求Iotrix API的逻辑，验证参数是否正确
    # 简化版可直接返回成功
    return {"title": f"Iotrix Solar ({data[CONF_DEVICE_ID]})"}

class IotrixSolarConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """处理配置流程"""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """处理用户初始化配置"""
        errors = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                return self.async_create_entry(title=info["title"], data=user_input)
            except Exception:
                errors["base"] = "cannot_connect"

        # 配置表单的字段定义
        data_schema = vol.Schema(
            {
                vol.Required(CONF_API_URL): str,
                vol.Required(CONF_DEVICE_ID): str,
                vol.Required(CONF_TOKEN): str,
                vol.Optional(CONF_USER_AGENT, default=DEFAULT_USER_AGENT): str,
                vol.Optional(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): int,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )