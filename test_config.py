import sys
sys.path.insert(0, '/opt/douyin-platform/src/backend')
from config import Config
print('FXG_BASE_URL:', Config.FXG_BASE_URL)
print('CREATOR_BASE_URL:', Config.CREATOR_BASE_URL)
print('FXG_COOKIES:', 'LOADED' if Config.FXG_COOKIES and Config.FXG_COOKIES != 'placeholder' else 'MISSING')
print('CREATOR_COOKIES:', 'LOADED' if Config.CREATOR_COOKIES and Config.CREATOR_COOKIES != 'placeholder' else 'MISSING')
print('FXG_SHOP_ID:', Config.FXG_SHOP_ID)
print('FXG_LOG_ID:', Config.FXG_LOG_ID)
print('API_KEY:', Config.API_KEY[:10] if Config.API_KEY else 'empty')
print('COMMON_HEADERS keys:', list(Config.COMMON_HEADERS.keys())[:5])
print('ALL CONFIG OK')
