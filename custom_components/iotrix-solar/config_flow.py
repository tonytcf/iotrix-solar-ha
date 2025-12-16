"""Config flow for Iotrix Solar integration - supports QR login and manual auth."""
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
    CONF_COOKIE,
    CONF_UPDATE_INTERVAL,
    CONF_LOGIN_MODE,
    CONF_QRCODE_API_URL,
    CONF_QRCODE_STATUS_API_URL,
    CONF_TOKEN_API_URL,
    DEFAULT_API_URL,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_LOGIN_MODE,
    DEFAULT_QRCODE_API_URL,
    DEFAULT_QRCODE_STATUS_API_URL,
    DEFAULT_TOKEN_API_URL,
)
from .api import (
    IotrixSolarApiClient,
    IotrixSolarApiError,
    IotrixSolarAuthError,
    IotrixSolarQrcodeError,
)

# 验证用户输入的配置是否有效（测试API连接）
async def validate_input(hass: HomeAssistant, data: dict) -> dict:
    """Validate config by fetching device data."""
    client = IotrixSolarApiClient(
        hass=hass,
        api_url=data[CONF_API_URL],
        device_id=data[CONF_DEVICE_ID],
        token=data.get(CONF_TOKEN),
        cookie=data.get(CONF_COOKIE),
        update_interval=data[CONF_UPDATE_INTERVAL],
        qrcode_api_url=data.get(CONF_QRCODE_API_URL),
        qrcode_status_api_url=data.get(CONF_QRCODE_STATUS_API_URL),
        token_api_url=data.get(CONF_TOKEN_API_URL),
    )
    try:
        # 测试获取设备数据
        await client.async_get_device_data()
        return {"title": f"Iotrix Solar ({data[CONF_DEVICE_ID]})"}
    finally:
        await client.async_close()

class IotrixSolarConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle config flow for Iotrix Solar."""

    VERSION = 1
    _temp_data: Dict[str, Any] = {}  # 存储临时配置数据

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Initial step: select login mode (QR code / manual auth)."""
        errors = {}

        if user_input is not None:
            # 存储基础配置，跳转至对应登录步骤
            self._temp_data = user_input
            if user_input[CONF_LOGIN_MODE] == "qrcode":
                return await self.async_step_qrcode()
            else:
                return await self.async_step_manual_auth()

        # 显示基础配置表单（API地址、设备ID、登录模式）
        data_schema = vol.Schema(
            {
                vol.Required(CONF_API_URL, default=DEFAULT_API_URL): str,
                vol.Required(CONF_DEVICE_ID): str,
                vol.Required(CONF_LOGIN_MODE, default=DEFAULT_LOGIN_MODE): vol.In(["qrcode", "manual"]),
                vol.Optional(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): vol.All(
                    vol.Coerce(int), vol.Range(min=10, max=300)
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description="Enter basic configuration and select login mode for Iotrix Solar",
        )

    async def async_step_qrcode(self, user_input: dict | None = None) -> FlowResult:
        """Step: WeChat QR code login (generate qrcode + poll status)."""
        errors = {}
        qrcode_data = {}

        # 初始化API客户端
        client = IotrixSolarApiClient(
            hass=self.hass,
            api_url=self._temp_data[CONF_API_URL],
            device_id=self._temp_data[CONF_DEVICE_ID],
            update_interval=self._temp_data[CONF_UPDATE_INTERVAL],
            qrcode_api_url=self._temp_data.get(CONF_QRCODE_API_URL, DEFAULT_QRCODE_API_URL),
            qrcode_status_api_url=self._temp_data.get(CONF_QRCODE_STATUS_API_URL, DEFAULT_QRCODE_STATUS_API_URL),
            token_api_url=self._temp_data.get(CONF_TOKEN_API_URL, DEFAULT_TOKEN_API_URL),
        )

        if user_input is not None:
            # 用户点击"完成扫码"，执行登录流程
            try:
                # 获取Token并存储
                token = await client.async_wechat_login(timeout=120)
                self._temp_data[CONF_TOKEN] = token
                # 验证配置并创建集成
                info = await validate_input(self.hass, self._temp_data)
                return self.async_create_entry(title=info["title"], data=self._temp_data)
            except IotrixSolarQrcodeError as e:
                errors["base"] = "qrcode_error"
                self.hass.logger.error(f"QR login error: {str(e)}")
            except IotrixSolarApiError as e:
                errors["base"] = "cannot_connect"
                self.hass.logger.error(f"API error: {str(e)}")
            finally:
                await client.async_close()

        # 生成二维码（用于表单显示）
        try:
            qrcode_data = await client.async_generate_qrcode()
            # 存储扫码API配置到临时数据
            self._temp_data[CONF_QRCODE_API_URL] = self._temp_data.get(CONF_QRCODE_API_URL, DEFAULT_QRCODE_API_URL)
            self._temp_data[CONF_QRCODE_STATUS_API_URL] = self._temp_data.get(CONF_QRCODE_STATUS_API_URL, DEFAULT_QRCODE_STATUS_API_URL)
            self._temp_data[CONF_TOKEN_API_URL] = self._temp_data.get(CONF_TOKEN_API_URL, DEFAULT_TOKEN_API_URL)
        except IotrixSolarQrcodeError as e:
            errors["base"] = "qrcode_generate_error"
            self.hass.logger.error(f"QR code generation error: {str(e)}")
        finally:
            await client.async_close()

        # 扫码登录表单（显示二维码 + 扫码按钮 + API配置）
        data_schema = vol.Schema(
            {
                vol.Optional("scan_confirm"): str,  # 扫码确认按钮（仅触发流程）
                vol.Optional(CONF_QRCODE_API_URL, default=DEFAULT_QRCODE_API_URL): str,
                vol.Optional(CONF_QRCODE_STATUS_API_URL, default=DEFAULT_QRCODE_STATUS_API_URL): str,
                vol.Optional(CONF_TOKEN_API_URL, default=DEFAULT_TOKEN_API_URL): str,
            }
        )

        # 构建二维码显示的HTML（优先使用Base64，其次使用URL）
        description_placeholders = {}
        if qrcode_data.get("qrcode_base64"):
            description_placeholders["qrcode"] = f'<img src="data:image/png;base64,{qrcode_data["qrcode_base64"]}" width="200" height="200"/>'
        elif qrcode_data.get("qrcode_url"):
            description_placeholders["qrcode"] = f'<img src="{qrcode_data["qrcode_url"]}" width="200" height="200"/>'
        else:
            description_placeholders["qrcode"] = "<b>Failed to load QR code</b>"

        return self.async_show_form(
            step_id="qrcode",
            data_schema=data_schema,
            errors=errors,
            description_placeholders=description_placeholders,
            description="Please scan the QR code with WeChat and click the button below to confirm:<br/>{qrcode}<br/><br/>If QR code expires, refresh the page to generate a new one.",
        )

    async def async_step_manual_auth(self, user_input: dict | None = None) -> FlowResult:
        """Step: Manual input token/cookie (backup mode)."""
        errors = {}

        if user_input is not None:
            # 合并临时数据与认证信息
            self._temp_data.update(user_input)
            # 验证至少有一个认证方式
            if not self._temp_data.get(CONF_TOKEN) and not self._temp_data.get(CONF_COOKIE):
                errors["base"] = "missing_auth"
            else:
                try:
                    # 验证配置并创建集成
                    info = await validate_input(self.hass, self._temp_data)
                    return self.async_create_entry(title=info["title"], data=self._temp_data)
                except IotrixSolarAuthError:
                    errors["base"] = "invalid_auth"
                except IotrixSolarApiError:
                    errors["base"] = "cannot_connect"

        # 手动认证表单（Token/Cookie二选一）
        data_schema = vol.Schema(
            {
                vol.Optional(CONF_TOKEN): str,
                vol.Optional(CONF_COOKIE): str,
            }
        )

        return self.async_show_form(
            step_id="manual_auth",
            data_schema=data_schema,
            errors=errors,
            description="Enter Token or Cookie (either one) for Iotrix Solar authentication",
        )