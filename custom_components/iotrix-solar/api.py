"""Iotrix Solar API Client"""
import time
import aiohttp
from typing import Dict, Optional, Any

class IotrixSolarApiError(Exception):
    """基础API异常"""
    pass

class IotrixSolarAuthError(IotrixSolarApiError):
    """认证失败异常（token失效）"""
    pass

class IotrixSolarApiClient:
    """Iotrix Solar API客户端"""
    def __init__(
        self,
        hass,
        api_url: str,
        device_id: str,
        token: str,
        user_agent: str,
        login_api_url: str = None,
        username: str = None,
        password: str = None,
    ):
        self.hass = hass
        self.api_url = api_url
        self.device_id = device_id
        self.token = token
        self.user_agent = user_agent
        # 登录相关参数（用于token刷新）
        self.login_api_url = login_api_url
        self.username = username
        self.password = password
        self.session: Optional[aiohttp.ClientSession] = None

    async def async_get_session(self) -> aiohttp.ClientSession:
        """获取复用的aiohttp会话（减少连接开销）"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={"User-Agent": self.user_agent}
            )
        return self.session

    async def async_login(self) -> str:
        """登录Iotrix平台，获取新token"""
        if not self.login_api_url or not self.username or not self.password:
            raise IotrixSolarAuthError("缺少登录参数，无法刷新token")
        
        session = await self.async_get_session()
        try:
            payload = {
                "username": self.username,
                "password": self.password,
                "timestamp": int(time.time())
            }
            async with session.post(
                self.login_api_url,
                json=payload,
                timeout=10
            ) as response:
                if response.status != 200:
                    raise IotrixSolarAuthError(f"登录失败，状态码：{response.status}")
                data = await response.json()
                new_token = data.get("data", {}).get("token")
                if not new_token:
                    raise IotrixSolarAuthError("登录响应中未获取到token")
                self.token = new_token  # 更新本地token
                return new_token
        except Exception as e:
            raise IotrixSolarAuthError(f"登录失败：{str(e)}") from e

    async def async_get_device_data(self) -> Dict[str, Any]:
        """获取设备数据（含token刷新重试）"""
        session = await self.async_get_session()
        params = {
            "deviceId": self.device_id,
            "time": int(time.time())
        }
        headers = {"token": self.token}

        try:
            async with session.get(
                self.api_url,
                params=params,
                headers=headers,
                timeout=10
            ) as response:
                # 处理token失效（假设平台返回401表示认证失败）
                if response.status == 401:
                    # 尝试刷新token
                    new_token = await self.async_login()
                    headers["token"] = new_token
                    # 重新请求数据
                    async with session.get(
                        self.api_url,
                        params=params,
                        headers=headers,
                        timeout=10
                    ) as retry_response:
                        if retry_response.status != 200:
                            raise IotrixSolarApiError(f"重试请求失败，状态码：{retry_response.status}")
                        return await self._parse_response(await retry_response.json())
                elif response.status != 200:
                    raise IotrixSolarApiError(f"请求失败，状态码：{response.status}")
                return await self._parse_response(await response.json())
        except IotrixSolarAuthError:
            # 登录失败则抛出原异常
            raise
        except Exception as e:
            raise IotrixSolarApiError(f"获取设备数据失败：{str(e)}") from e

    async def _parse_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """解析API响应，统一数据格式（容错处理）"""
        # 处理空数据、字段缺失的情况
        data = data.get("data", {})
        return {
            "power": data.get("power", 0.0),
            "voltage": data.get("voltage", 0.0),
            "daily_generation": data.get("dailyGen", 0.0),
            "total_generation": data.get("totalGen", 0.0),
            "update_time": time.time()
        }

    async def async_close(self):
        """关闭aiohttp会话"""
        if self.session and not self.session.closed:
            await self.session.close()