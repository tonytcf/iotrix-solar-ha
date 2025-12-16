"""Constants for Iotrix Solar integration."""
from homeassistant.const import Platform

# 集成核心配置
DOMAIN = "iotrix_solar"
PLATFORMS = [Platform.SENSOR, Platform.CAMERA]
VERSION = "1.0.0"

# 配置参数键名
CONF_API_URL = "api_url"
CONF_DEVICE_ID = "device_id"
CONF_TOKEN = "token"
CONF_COOKIE = "cookie"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_LOGIN_MODE = "login_mode"
# 扫码登录相关API配置
CONF_QRCODE_API_URL = "qrcode_api_url"
CONF_QRCODE_STATUS_API_URL = "qrcode_status_api_url"
CONF_TOKEN_API_URL = "token_api_url"

# 默认值（根据抓包结果调整，以下为通用示例）
DEFAULT_API_URL = "https://portal.iotrix.net/api"
DEFAULT_UPDATE_INTERVAL = 60  # 数据更新间隔（秒）
DEFAULT_LOGIN_MODE = "qrcode"  # 默认扫码登录
# 扫码登录API默认地址（需替换为抓包的实际地址）
DEFAULT_QRCODE_API_URL = "https://portal.iotrix.net/api/v1/qrcode/generate"
DEFAULT_QRCODE_STATUS_API_URL = "https://portal.iotrix.net/api/v1/qrcode/status"
DEFAULT_TOKEN_API_URL = "https://portal.iotrix.net/api/v1/token/refresh"

# 扫码状态常量
QRCODE_STATUS_UNSCANNED = "unscanned"
QRCODE_STATUS_SCANNED = "scanned"
QRCODE_STATUS_CONFIRMED = "confirmed"
QRCODE_STATUS_EXPIRED = "expired"

# 传感器类型定义（适配Iotrix数据字段）
SENSOR_TYPES = {
    "pv_power": {
        "name": "PV功率",
        "unit": "W",
        "icon": "mdi:solar-power",
        "state_class": "measurement",
    },
    "daily_generation": {
        "name": "日发电量",
        "unit": "kWh",
        "icon": "mdi:counter",
        "state_class": "total_increasing",
    },
    "total_generation": {
        "name": "总发电量",
        "unit": "kWh",
        "icon": "mdi:counter",
        "state_class": "total_increasing",
    },
    "battery_soc": {
        "name": "电池容量",
        "unit": "%",
        "icon": "mdi:battery",
        "state_class": "measurement",
    },
    "token_status": {
        "name": "Token状态",
        "unit": None,
        "icon": "mdi:check-circle",
        "state_class": None,
    },
}