"""Camera platform for Iotrix Solar - displays WeChat QR code for login."""
from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .helpers import base64_to_bytes

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Iotrix Solar QR code camera."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    client = hass.data[DOMAIN][entry.entry_id]["client"]
    async_add_entities([IotrixSolarQrcodeCamera(coordinator, entry, client)])

class IotrixSolarQrcodeCamera(Camera):
    """QR code camera entity for WeChat login."""

    def __init__(self, coordinator, entry, client):
        """Initialize the camera."""
        super().__init__()
        self._coordinator = coordinator
        self._entry = entry
        self._client = client
        self._attr_name = "Iotrix Solar QR Code"
        self._attr_unique_id = f"{entry.entry_id}_qrcode_camera"
        self._attr_entity_category = "diagnostic"  # 归类为诊断实体

    async def async_camera_image(self, width: int = None, height: int = None) -> bytes:
        """Return the QR code image as bytes (refresh every time)."""
        try:
            # 重新生成二维码（确保最新）
            qrcode_data = await self._client.async_generate_qrcode()
            if qrcode_data.get("qrcode_base64"):
                return base64_to_bytes(qrcode_data["qrcode_base64"])
            elif qrcode_data.get("qrcode_url"):
                # 若为URL，下载图片（可选，需添加aiohttp请求）
                return b""
            return b""
        except Exception as e:
            self._coordinator.hass.logger.error(f"Failed to get QR code image: {str(e)}")
            return b""

    @property
    def is_streaming(self) -> bool:
        """Return True (camera is always available)."""
        return True