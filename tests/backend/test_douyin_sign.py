"""Unit tests for Douyin signing logic."""

import pytest
import json
from douyin_sign import DouyinSigner, sign_request, get_signer


class TestDouyinSigner:
    """Test DouyinSigner class."""

    def setup_method(self):
        """Reset singleton before each test."""
        import douyin_sign
        douyin_sign._default_signer = None

    def test_signer_singleton(self):
        """Test that get_signer returns singleton."""
        signer1 = get_signer()
        signer2 = get_signer()
        assert signer1 is signer2

    def test_signer_with_custom_ua(self):
        """Test signer with custom User-Agent."""
        signer = get_signer("Custom UA/1.0")
        assert signer.ua == "Custom UA/1.0"

    def test_sanitize_ua_normal(self):
        """Test UA sanitization with normal input."""
        signer = DouyinSigner()
        ua = signer._sanitize_ua("Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        assert ua == "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"

    def test_sanitize_ua_strips_non_ascii(self):
        """Test UA sanitization removes non-printable characters."""
        signer = DouyinSigner()
        ua = signer._sanitize_ua("Mozilla/5.0\x00\x01\x7f")
        assert "\x00" not in ua
        assert "\x01" not in ua
        assert "\x7f" not in ua

    def test_sanitize_ua_limits_length(self):
        """Test UA sanitization limits length to 500."""
        signer = DouyinSigner()
        long_ua = "A" * 1000
        ua = signer._sanitize_ua(long_ua)
        assert len(ua) == 500

    def test_sanitize_url_normal(self):
        """Test URL sanitization with normal input."""
        signer = DouyinSigner()
        url = signer._sanitize_url("https://fxg.jinritemai.com/api/test")
        assert url == "https://fxg.jinritemai.com/api/test"

    def test_sanitize_params_normal(self):
        """Test params sanitization with normal input."""
        signer = DouyinSigner()
        params = {"page": 1, "size": 20, "keyword": "test"}
        clean = signer._sanitize_params(params)
        assert clean == {"page": "1", "size": "20", "keyword": "test"}

    def test_sanitize_params_removes_invalid_keys(self):
        """Test params sanitization removes invalid key characters."""
        signer = DouyinSigner()
        params = {"valid_key": "value", "invalid-key": "value2", "key@#$": "value3"}
        clean = signer._sanitize_params(params)
        assert "valid_key" in clean
        assert "invalid-key" in clean  # hyphens are allowed in keys
        assert "key" in clean  # special chars removed

    def test_sanitize_params_limits_value_length(self):
        """Test params sanitization limits value length to 1000."""
        signer = DouyinSigner()
        params = {"key": "A" * 2000}
        clean = signer._sanitize_params(params)
        assert len(clean["key"]) == 1000

    def test_sanitize_token(self):
        """Test token sanitization."""
        signer = DouyinSigner()
        token = signer._sanitize_token("  test_token  ")
        assert token == "test_token"

    def test_generate_sign_params_basic(self):
        """Test basic sign params generation."""
        signer = DouyinSigner()
        url = "https://fxg.jinritemai.com/product/tproduct/list"
        params = {
            "page": 1,
            "pageSize": 20,
            "appid": 1,
            "_bid": "ffa_product",
        }
        tokens = {
            "__token": "test_token",
            "msToken": "test_ms",
            "verifyFp": "verify_test",
            "fp": "verify_test",
        }
        result = signer.generate_sign_params(url, params, tokens)

        assert "__token" in result
        assert "msToken" in result
        assert "a_bogus" in result
        assert "verifyFp" in result
        assert "fp" in result
        assert "_t" in result

        # Check that existing tokens are preserved
        assert result["__token"] == "test_token"
        assert result["msToken"] == "test_ms"
        assert result["verifyFp"] == "verify_test"
        assert result["fp"] == "verify_test"

        # Check timestamp is present and valid
        assert result["_t"].isdigit()
        timestamp = int(result["_t"])
        import time
        assert abs(timestamp - int(time.time())) < 5  # within 5 seconds

    def test_generate_sign_params_generates_new_tokens(self):
        """Test that new tokens are generated when not provided."""
        signer = DouyinSigner()
        url = "https://fxg.jinritemai.com/product/tproduct/list"
        params = {"page": 1}
        result = signer.generate_sign_params(url, params, {})

        # Should have generated new tokens
        assert result["msToken"] != ""
        assert result["verifyFp"].startswith("verify_msu_")
        assert result["fp"].startswith("verify_msu_")

    def test_generate_sign_params_a_bogus_format(self):
        """Test a_bogus format is correct (base64 of md5:timestamp)."""
        signer = DouyinSigner()
        url = "https://fxg.jinritemai.com/product/tproduct/list"
        params = {"page": 1}
        result = signer.generate_sign_params(url, params, {})

        import base64
        a_bogus = result["a_bogus"]
        decoded = base64.b64decode(a_bogus).decode()
        parts = decoded.split(":")
        assert len(parts) == 2
        md5_hash = parts[0]
        timestamp = parts[1]
        assert len(md5_hash) == 32  # MD5 hex length
        assert timestamp.isdigit()

    def test_sign_request_convenience_function(self):
        """Test the sign_request convenience function."""
        url = "https://fxg.jinritemai.com/product/tproduct/list"
        params = {"page": 1}
        tokens = {"__token": "test"}
        result = sign_request(url, params, tokens)

        assert "__token" in result
        assert result["__token"] == "test"

    def test_consistent_signing_same_inputs(self):
        """Test that same inputs produce consistent a_bogus (except timestamp)."""
        signer = DouyinSigner()
        url = "https://fxg.jinritemai.com/product/tproduct/list"
        params = {"page": 1, "size": 20}
        tokens = {"__token": "fixed_token", "msToken": "fixed_ms"}

        # First call
        result1 = signer.generate_sign_params(url, params, tokens)
        # Manually increment timestamp for second call to simulate time passing
        import time
        original_time = time.time
        try:
            time.time = lambda: original_time() + 1
            result2 = signer.generate_sign_params(url, params, tokens)
        finally:
            time.time = original_time

        # Tokens should be same (provided)
        assert result1["__token"] == result2["__token"]
        assert result1["msToken"] == result2["msToken"]
        # Timestamp should be different
        assert result1["_t"] != result2["_t"]
        # a_bogus should be different due to timestamp
        assert result1["a_bogus"] != result2["a_bogus"]


class TestSignRequestIntegration:
    """Integration tests for sign_request with realistic data."""

    def test_realistic_product_list_request(self):
        """Test signing a realistic product list request."""
        url = "https://fxg.jinritemai.com/product/tproduct/list"
        params = {
            "page": 1,
            "pageSize": 100,
            "appid": 1,
            "_bid": "ffa_product",
            "aid": 4272,
            "_lid": 104476165896,
        }
        tokens = {
            "__token": "abc123",
            "msToken": "xyz789",
            "verifyFp": "verify_fp_value",
            "fp": "fp_value",
        }

        result = sign_request(url, params, tokens)

        # All required fields present
        required_fields = ["__token", "msToken", "a_bogus", "verifyFp", "fp", "_t"]
        for field in required_fields:
            assert field in result, f"Missing field: {field}"

        # Values preserved
        assert result["__token"] == "abc123"
        assert result["msToken"] == "xyz789"

    def test_special_characters_in_params(self):
        """Test signing with special characters in params."""
        signer = DouyinSigner()
        url = "https://fxg.jinritemai.com/api/search"
        params = {
            "keyword": "test & special <> chars",
            "category": "category_1",
        }
        tokens = {"__token": "test"}

        result = signer.generate_sign_params(url, params, tokens)
        assert "a_bogus" in result
        assert result["_t"].isdigit()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])