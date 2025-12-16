"""Iotrix Solar API Client - handles WeChat QR login and data fetching."""
import asyncio
import aiohttp
from typing import Dict, Any, Optional
from homeassistant.core import HomeAssistant

from .const import (
    QRCODE_STATUS_UNSCANNED,
    QRCODE_STATUS_SCANNED,
    QRCODE_STATUS_CONFIRMED,
    QRCODE_STATUS_EXPIRED,
)
from .helpers import base64_to_bytes

# 异常定义
class IotrixSolarApiError(Exception):
    """Base exception for Iotrix API errors."""

class IotrixSolarAuthError(IotrixSolarApiError):
    """Authentication error (token/cookie expired/invalid)."""

class IotrixSolarQrcodeError(IotrixSolarApiError):
    """QR code related error (generation/polling failed)."""

class IotrixSolarApiClient:
    """Async API client for Iotrix Solar."""

    def __init__(
        self,
        hass: HomeAssistant,
        api_url: str,
        device_id: str,
        token: str = None,
        cookie: str = None,
        update_interval: int = 60,
        qrcode_api_url: str = None,
        qrcode_status_api_url: str = None,
        token_api_url: str = None,
    ):
        self.hass = hass
        self.api_url = api_url.rstrip("/")
        self.device_id = device_id
        self.token = token
        self.cookie = cookie
        self.update_interval = update_interval
        # 扫码登录API配置
        self.qrcode_api_url = qrcode_api_url.rstrip("/") if qrcode_api_url else None
        self.qrcode_status_api_url = qrcode_status_api_url.rstrip("/") if qrcode_status_api_url else None
        self.token_api_url = token_api_url.rstrip("/") if token_api_url else None
        # 会话与二维码状态
        self._session: Optional[aiohttp.ClientSession] = None
        self.qrcode_id: Optional[str] = None
        self.qrcode_base64: Optional[str] = None
        self.qrcode_url: Optional[str] = None

    async def async_get_session(self) -> aiohttp.ClientSession:
        """Get a reusable aiohttp session (reduces connection overhead)."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )
        return self._session

    async def async_get_headers(self) -> Dict[str, str]:
        """Build request headers with authentication (token/cookie)."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        # Token认证（优先使用Token）
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"  # 需匹配API的Token格式（如Token xxx）
        # Cookie认证（备用）
        if self.cookie:
            headers["Cookie"] = self.cookie
        return headers

    async def async_generate_qrcode(self) -> Dict[str, Any]:
        """Generate WeChat QR code for login (returns qrcode data)."""
        if not self.qrcode_api_url:
            raise IotrixSolarQrcodeError("QR code API URL is not configured")

        session = await self.async_get_session()
        headers = await self.async_get_headers()

        # 发送二维码生成请求（根据抓包结果调整GET/POST）
        try:
            async with session.get(
                self.qrcode_api_url, headers=headers, timeout=10
            ) as response:
                if response.status != 200:
                    raise IotrixSolarQrcodeError(f"QR code generation failed (status: {response.status})")
                data = await response.json()
                qrcode_data = data.get("data", {})

                # 提取二维码核心信息（根据抓包的响应字段调整）
                self.qrcode_id = qrcode_data.get("qrcodeId") or qrcode_data.get("ticket") or qrcode_data.get("id")
                self.qrcode_base64 = qrcode_data.get("qrcodeBase64") or qrcode_data.get("base64")
                self.qrcode_url = qrcode_data.get("qrcodeUrl") or qrcode_data.get("url")

                if not self.qrcode_id:
                    raise IotrixSolarQrcodeError("QR code ID not found in API response")

                return {
                    "qrcode_id": self.qrcode_id,
                    "qrcode_base64": self.qrcode_base64,
                    "qrcode_url": self.qrcode_url,
                }
        except aiohttp.ClientError as e:
            raise IotrixSolarQrcodeError(f"Network error: {str(e)}") from e

    async def async_poll_qrcode_status(self) -> Dict[str, Any]:
        """Poll QR code scan status (returns status and temp code if confirmed)."""
        if not self.qrcode_id or not self.qrcode_status_api_url:
            raise IotrixSolarQrcodeError("QR code ID or status API URL is missing")

        session = await self.async_get_session()
        headers = await self.async_get_headers()
        params = {"qrcodeId": self.qrcode_id}  # 根据抓包的参数调整（如ticket=self.qrcode_id）

        try:
            async with session.get(
                self.qrcode_status_api_url, headers=headers, params=params, timeout=10
            ) as response:
                if response.status != 200:
                    raise IotrixSolarQrcodeError(f"QR code status fetch failed (status: {response.status})")
                data = await response.json()
                status_data = data.get("data", {})

                # 提取状态（根据抓包的响应字段调整）
                status = status_data.get("status", QRCODE_STATUS_UNSCANNED)
                temp_code = status_data.get("code") or status_data.get("authCode")
                expired = status_data.get("expired", False) or status == QRCODE_STATUS_EXPIRED

                return {
                    "status": status,
                    "temp_code": temp_code,
                    "expired": expired,
                }
        except aiohttp.ClientError as e:
            raise IotrixSolarQrcodeError(f"Network error: {str(e)}") from e

    async def async_exchange_code_for_token(self, temp_code: str) -> str:
        """Exchange temporary scan code for access token."""
        if not self.token_api_url or not temp_code:
            raise IotrixSolarAuthError("Token API URL or temporary code is missing")

        session = await self.async_get_session()
        headers = await self.async_get_headers()
        payload = {"code": temp_code, "deviceId": self.device_id}  # 根据抓包的请求体调整

        try:
            async with session.post(
                self.token_api_url, headers=headers, json=payload, timeout=10
            ) as response:
                if response.status != 200:
                    raise IotrixSolarAuthError(f"Token exchange failed (status: {response.status})")
                data = await response.json()
                token_data = data.get("data", {})

                # 提取Token（根据抓包的响应字段调整）
                token = token_data.get("token") or token_data.get("accessToken") or token_data.get("jwt")
                if not token:
                    raise IotrixSolarAuthError("Token not found in API response")

                # 更新客户端Token
                self.token = token
                return token
        except aiohttp.ClientError as e:
            raise IotrixSolarAuthError(f"Network error: {str(e)}") from e

    async def async_wechat_login(self, timeout: int = 120) -> str:
        """Complete WeChat QR login flow (generate qrcode → poll status → get token)."""
        # Step 1: Generate QR code
        await self.async_generate_qrcode()

        # Step 2: Poll status until confirmed or timeout
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < timeout:
            status_data = await self.async_poll_qrcode_status()

            # Handle expired QR code
            if status_data["expired"]:
                raise IotrixSolarQrcodeError("QR code expired, please generate a new one")

            # Handle confirmed status (scan + confirm)
            if status_data["status"] == QRCODE_STATUS_CONFIRMED and status_data["temp_code"]:
                # Step 3: Exchange code for token
                token = await self.async_exchange_code_for_token(status_data["temp_code"])
                return token

            # Wait 2 seconds before next poll
            await asyncio.sleep(2)

        # Timeout
        raise IotrixSolarQrcodeError(f"QR code login timeout (>{timeout}s)")

    async def async_get_device_data(self) -> Dict[str, Any]:
        """Fetch solar device data from Iotrix API (core business logic)."""
        session = await self.async_get_session()
        headers = await self.async_get_headers()
        # 设备数据API地址（根据抓包结果调整，如/api/v1/device/data）
        data_url = f"{self.api_url}/device/data?deviceId={self.device_id}"

        try:
            async with session.get(
                data_url, headers=headers, timeout=10
            ) as response:
                # Handle auth errors
                if response.status in (401, 403):
                    raise IotrixSolarAuthError("Token/Cookie expired or invalid")
                if response.status != 200:
                    raise IotrixSolarApiError(f"Data fetch failed (status: {response.status})")

                # Parse data (根据抓包的响应字段调整)
                raw_data = await response.json()
                data = raw_data.get("data", {})
                return {
                    "pv_power": float(data.get("pvPower", 0.0)),
                    "daily_generation": float(data.get("dailyGen", 0.0)),
                    "total_generation": float(data.get("totalGen", 0.0)),
                    "battery_soc": float(data.get("batterySoc", 0.0)),
                    "token_status": "valid" if not response.status in (401, 403) else "invalid",
                }
        except aiohttp.ClientError as e:
            raise IotrixSolarApiError(f"Network error: {str(e)}") from e

    async def async_close(self) -> None:
        """Close the aiohttp session to free resources."""
        if self._session and not self._session.closed:
            await self._session.close()