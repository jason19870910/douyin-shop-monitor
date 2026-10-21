"""Unit tests for fetcher module (pure logic, no external deps)."""

import pytest
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# Mock Redis cache BEFORE any imports
# We need to patch the redis_cache module in sys.modules before fetcher is imported
mock_cache = MagicMock()
mock_cache.get.return_value = None
mock_cache.set.return_value = True

# Create a mock redis_cache module
mock_redis_cache = MagicMock()
mock_redis_cache.get_cache = lambda: mock_cache
mock_redis_cache.RedisCache = MagicMock(return_value=mock_cache)

# Inject into sys.modules BEFORE importing fetcher
sys.modules['services.redis_cache'] = mock_redis_cache

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Now import fetcher - it will use our mocked redis_cache
from services.fetcher import (
    parse_cookies,
    save_json_file,
    load_json_file,
    get_fxg_cookies,
    get_creator_cookies,
    get_data_with_fallback,
    init_compliance_data,
    load_all_data,
    save_all_data,
    DEFAULT_ALERT_CONFIG,
    DEFAULT_ALERT_DOUYIN_CONFIG,
    DEFAULT_ALERT_DIAN_CONFIG,
    DEFAULT_AUTH_CONFIG,
    DEFAULT_VIDEOS,
    DEFAULT_ACCOUNTS,
    DEFAULT_COMPLIANCE,
    DEFAULT_MEDIA,
    cache,
)
import services.fetcher as fetcher_module


class TestParseCookies:
    """Test cookie parsing utilities."""

    def test_parse_empty_string(self):
        assert parse_cookies("") == {}
        assert parse_cookies(None) == {}

    def test_parse_simple_cookies(self):
        cookie_str = "a=1; b=2; c=3"
        result = parse_cookies(cookie_str)
        assert result == {"a": "1", "b": "2", "c": "3"}

    def test_parse_cookies_with_spaces(self):
        cookie_str = "a=1; b=2; c=3"
        result = parse_cookies(cookie_str)
        assert result == {"a": "1", "b": "2", "c": "3"}

    def test_parse_cookies_with_special_chars(self):
        cookie_str = "session=abc123; token=xyz%3D789; path=/"
        result = parse_cookies(cookie_str)
        assert result["session"] == "abc123"
        assert result["token"] == "xyz%3D789"
        assert result["path"] == "/"

    def test_parse_cookies_no_value(self):
        cookie_str = "a=1; b="
        result = parse_cookies(cookie_str)
        assert result == {"a": "1", "b": ""}


class TestSaveJsonFile:
    """Test JSON file saving."""

    def test_save_json_file_success(self, tmp_path):
        file_path = tmp_path / "test.json"
        data = {"key": "value", "number": 123, "list": [1, 2, 3]}
        save_json_file(file_path, data)
        assert file_path.exists()
        with open(file_path, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
        assert loaded == data

    def test_save_json_file_unicode(self, tmp_path):
        file_path = tmp_path / "test_unicode.json"
        data = {"name": "测试商品", "description": "包含中文"}
        save_json_file(file_path, data)
        assert file_path.exists()
        with open(file_path, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
        assert loaded == data


class TestLoadJsonFile:
    """Test JSON file loading with optional Pydantic validation."""

    def test_load_existing_file(self, tmp_path):
        file_path = tmp_path / "existing.json"
        data = {"test": "value"}
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        result = load_json_file(file_path, default={})
        assert result == data

    def test_load_nonexistent_file_returns_default(self, tmp_path):
        file_path = tmp_path / "nonexistent.json"
        default = {"default": True}
        result = load_json_file(file_path, default=default)
        assert result == default

    def test_load_invalid_json_returns_default(self, tmp_path):
        file_path = tmp_path / "invalid.json"
        file_path.write_text("not valid json")
        default = {"fallback": True}
        result = load_json_file(file_path, default=default)
        assert result == default


class TestGetFxgCookies:
    """Test FXG cookie retrieval."""

    @patch('services.fetcher._read_secret')
    def test_get_fxg_cookies_from_secret(self, mock_read_secret):
        mock_read_secret.return_value = "session=abc; token=xyz"
        result = get_fxg_cookies()
        assert result == {"session": "abc", "token": "xyz"}

    @patch('services.fetcher._read_secret')
    def test_get_fxg_cookies_empty(self, mock_read_secret):
        mock_read_secret.return_value = ""
        result = get_fxg_cookies()
        assert result == {}


class TestGetCreatorCookies:
    """Test Creator cookie retrieval."""

    @patch('services.fetcher._read_secret')
    def test_get_creator_cookies_from_secret(self, mock_read_secret):
        mock_read_secret.return_value = "session=creator123"
        result = get_creator_cookies()
        assert result == {"session": "creator123"}


class TestDefaultConfigs:
    """Test default configuration constants."""

    def test_default_alert_config_structure(self):
        assert 'sales_drop_threshold' in DEFAULT_ALERT_CONFIG
        assert 'conversion_drop_threshold' in DEFAULT_ALERT_CONFIG
        assert 'inventory_low_threshold' in DEFAULT_ALERT_CONFIG
        assert 'notification_email' in DEFAULT_ALERT_CONFIG
        assert 'enabled' in DEFAULT_ALERT_CONFIG
        assert DEFAULT_ALERT_CONFIG['enabled'] is True

    def test_default_alert_douyin_config_structure(self):
        assert 'video_view_drop_threshold' in DEFAULT_ALERT_DOUYIN_CONFIG
        assert 'video_like_drop_threshold' in DEFAULT_ALERT_DOUYIN_CONFIG
        assert 'creator_follower_drop_threshold' in DEFAULT_ALERT_DOUYIN_CONFIG
        assert 'notification_email' in DEFAULT_ALERT_DOUYIN_CONFIG
        assert 'enabled' in DEFAULT_ALERT_DOUYIN_CONFIG

    def test_default_alert_dian_config_structure(self):
        assert 'product_sales_drop_threshold' in DEFAULT_ALERT_DIAN_CONFIG
        assert 'order_refund_rate_threshold' in DEFAULT_ALERT_DIAN_CONFIG
        assert 'compliance_risk_threshold' in DEFAULT_ALERT_DIAN_CONFIG
        assert 'notification_email' in DEFAULT_ALERT_DIAN_CONFIG
        assert 'enabled' in DEFAULT_ALERT_DIAN_CONFIG

    def test_default_auth_config_structure(self):
        assert 'douyin_app_id' in DEFAULT_AUTH_CONFIG
        assert 'douyin_app_secret' in DEFAULT_AUTH_CONFIG
        assert 'redirect_uri' in DEFAULT_AUTH_CONFIG
        assert 'authorized' in DEFAULT_AUTH_CONFIG
        assert 'access_token' in DEFAULT_AUTH_CONFIG
        assert 'refresh_token' in DEFAULT_AUTH_CONFIG
        assert 'expires_at' in DEFAULT_AUTH_CONFIG
        assert 'scope' in DEFAULT_AUTH_CONFIG
        assert DEFAULT_AUTH_CONFIG['authorized'] is False

    def test_default_empty_lists(self):
        assert DEFAULT_VIDEOS == []
        assert DEFAULT_ACCOUNTS == []
        assert DEFAULT_COMPLIANCE == []
        assert DEFAULT_MEDIA == []


class TestAlertConfigSwitchPersistence:
    """告警开关（enabled）不得因缓存过期而"自动重新启用"的回归测试。

    根因：告警配置写 Redis 带 1 小时 TTL，且缓存未命中时直接回退
    enabled=True 的默认配置，用户关闭的开关约一小时后重新启用。
    修复：缓存写入无 TTL，读取链为 缓存 -> 持久化文件 -> 默认配置。
    """

    def _run_get(self, key, func_name, cache_hit):
        """Run fetcher.<func_name> with cache.get mocked as cache_hit."""
        mock = MagicMock()
        mock.get.return_value = cache_hit
        with patch.object(fetcher_module, "_CONFIG_FILES",
                          {**fetcher_module._CONFIG_FILES, key: self._file}), \
             patch.object(fetcher_module, "cache", mock):
            func = getattr(fetcher_module, func_name)
            result = func(key) if func_name == "get_config" else func()
        return result, mock

    @pytest.fixture(autouse=True)
    def _tmp_cfg_file(self, tmp_path):
        self._file = tmp_path / "alert_config.json"
        yield

    def test_get_config_cache_hit(self):
        cached = dict(DEFAULT_ALERT_CONFIG, enabled=False)
        result, mock = self._run_get("alert_config", "get_config", cached)
        assert result["enabled"] is False
        mock.set.assert_not_called()

    def test_get_config_falls_back_to_persisted_file(self):
        persisted = dict(DEFAULT_ALERT_DOUYIN_CONFIG, enabled=False)
        self._file.write_text(json.dumps(persisted), encoding="utf-8")
        result, mock = self._run_get("alert_douyin_config", "get_config", None)
        assert result["enabled"] is False
        mock.set.assert_called_once_with(
            fetcher_module.CACHE_KEYS["alert_douyin_config"], persisted, ttl=None
        )

    def test_get_config_uses_default_only_without_cache_and_file(self):
        result, _ = self._run_get("alert_dian_config", "get_config", None)
        assert result["enabled"] is True

    def test_get_douyin_alert_config_keeps_disabled_switch(self):
        persisted = dict(DEFAULT_ALERT_DOUYIN_CONFIG, enabled=False)
        self._file.write_text(json.dumps(persisted), encoding="utf-8")
        result, mock = self._run_get("alert_douyin_config", "get_douyin_alert_config", None)
        assert result["enabled"] is False
        mock.set.assert_called_once_with(
            fetcher_module.CACHE_KEYS["alert_douyin_config"], persisted, ttl=None
        )

    def test_get_dian_alert_config_keeps_disabled_switch(self):
        persisted = dict(DEFAULT_ALERT_DIAN_CONFIG, enabled=False)
        self._file.write_text(json.dumps(persisted), encoding="utf-8")
        result, mock = self._run_get("alert_dian_config", "get_dian_alert_config", None)
        assert result["enabled"] is False
        mock.set.assert_called_once_with(
            fetcher_module.CACHE_KEYS["alert_dian_config"], persisted, ttl=None
        )

    def test_set_config_persists_without_ttl_and_writes_file(self):
        value = dict(DEFAULT_ALERT_CONFIG, enabled=False)
        mock = MagicMock()
        mock.get.return_value = None
        with patch.object(fetcher_module, "_CONFIG_FILES",
                          {**fetcher_module._CONFIG_FILES, "alert_config": self._file}), \
             patch.object(fetcher_module, "cache", mock):
            fetcher_module.set_config("alert_config", value)
        mock.set.assert_called_once_with(
            fetcher_module.CACHE_KEYS["alert_config"], value, ttl=None
        )
        assert json.loads(self._file.read_text(encoding="utf-8"))["enabled"] is False


# Tests for get_data_with_fallback, init_compliance_data, load_all_data, save_all_data
# require Redis connection and are moved to integration tests


if __name__ == "__main__":
    pytest.main([__file__, "-v"])