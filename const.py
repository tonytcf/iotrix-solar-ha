"""Constants for Iotrix Solar integration."""
from homeassistant.const import Platform

# 集成域名
DOMAIN = "iotrix_solar"
# 支持的平台
PLATFORMS = [Platform.SENSOR]
# 配置参数的键名
CONF_API_URL = "api_url"
CONF_DEVICE_ID = "device_id"
CONF_TOKEN = "token"
CONF_USER_AGENT = "user_agent"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_LOGIN_API_URL = "login_api_url"  # 新增：登录API地址
CONF_USERNAME = "username"  # 新增：平台用户名
CONF_PASSWORD = "password"  # 新增：平台密码
# 默认值
DEFAULT_UPDATE_INTERVAL = 60  # 60秒
DEFAULT_USER_AGENT = "Mozilla/5.0 (Mobile; Android 13; Pixel 7) AppleWebKit/537.36"
# 传感器唯一标识前缀
SENSOR_PREFIX = "iotrix_solar"
# 缓存键名
CACHE_KEY = "iotrix_solar_data_cache"