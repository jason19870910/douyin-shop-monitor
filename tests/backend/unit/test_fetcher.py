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


# Tests for get_data_with_fallback, init_compliance_data, load_all_data, save_all_data
# require Redis connection and are moved to integration tests


if __name__ == "__main__":
    pytest.main([__file__, "-v"])