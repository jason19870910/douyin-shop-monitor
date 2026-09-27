import sys
sys.path.insert(0, '/app')
from config.settings import Config
print('FXG_ORDER_AID:', getattr(Config, 'FXG_ORDER_AID', 'missing'))
