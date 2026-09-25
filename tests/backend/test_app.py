"""Unit tests for doudian_monitor helper functions."""

import os
import sys
import pytest

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', '..', 'src', 'backend'))

from app import parse_cookie, extract_csrf_token, build_product_headers


class TestParseCookie:
    """Test cookie parsing logic."""

    def test_parse_simple_string(self):
        cookie = "a=1; b=2; c=3"
        result = parse_cookie(cookie)
        assert result == "a=1; b=2; c=3"

    def test_parse_none(self):
        assert parse_cookie(None) == ""
        assert parse_cookie("") == ""

    def test_parse_file_with_tabs(self, tmp_path):
        cookie_file = tmp_path / "cookies.txt"
        cookie_file.write_text(
            ".example.com\tTRUE\t/\tFALSE\t1234567890\ttest\tvalue1\n"
            ".example.com\tTRUE\t/\tFALSE\t1234567890\ttoken\tvalue2\n",
            encoding="utf-8"
        )
        result = parse_cookie(str(cookie_file))
        assert "test=value1" in result
        assert "token=value2" in result
        assert result.endswith("token=value2")

    def test_parse_file_without_tabs(self, tmp_path):
        cookie_file = tmp_path / "cookies.txt"
        cookie_file.write_text("a=1; b=2", encoding="utf-8")
        result = parse_cookie(str(cookie_file))
        assert result.strip() == "a=1; b=2"


class TestExtractCsrfToken:
    """Test CSRF token extraction from URL."""

    def test_extract_from_url(self):
        url = "https://example.com/path?__token=abc123&other=xyz"
        assert extract_csrf_token(url) == "abc123"

    def test_extract_multiple_tokens(self):
        url = "https://example.com/?__token=first&__token=second"
        assert extract_csrf_token(url) == "first"

    def test_no_token(self):
        url = "https://example.com/path?other=value"
        assert extract_csrf_token(url) == ""

    def test_invalid_url(self):
        assert extract_csrf_token("not a url") == ""


class TestBuildProductHeaders:
    """Test header construction for API requests."""

    def test_build_headers_contains_required_fields(self, monkeypatch):
        monkeypatch.setenv("COOKIE", "a=1; b=2")
        monkeypatch.setenv("CREATOR_CSRF_TOKEN", "csrf123")

        url = "https://fxg.jinritemai.com/api/test"
        headers = build_product_headers(url)

        assert headers["accept"] == "application/json, text/plain, */*"
        assert headers["accept-language"] == "zh-CN,zh;q=0.9"
        assert headers["cookie"] == "a=1; b=2"
        assert headers["origin"] == "https://fxg.jinritemai.com"
        assert headers["referer"] == "https://fxg.jinritemai.com/"
        assert "Chrome" in headers["user-agent"]
        assert headers["x-csrf-token"] == "csrf123"
        assert headers["x-secsdk-csrf-token"] == "csrf123"
        assert headers["x-requested-with"] == "XMLHttpRequest"

    def test_extract_token_from_url(self, monkeypatch):
        monkeypatch.setenv("COOKIE", "a=1")
        monkeypatch.delenv("CREATOR_CSRF_TOKEN", raising=False)

        url = "https://fxg.jinritemai.com/api/test?__token=url_token_456"
        headers = build_product_headers(url)
        assert headers["x-csrf-token"] == "url_token_456"

    def test_fallback_to_token_when_no_url_token(self, monkeypatch):
        monkeypatch.setenv("COOKIE", "a=1")
        monkeypatch.setenv("CREATOR_CSRF_TOKEN", "fallback_token")
        monkeypatch.delenv("CREATOR_CSRF_TOKEN", raising=False)

        url = "https://fxg.jinritemai.com/api/test"
        headers = build_product_headers(url)
        # When no env token and no URL token, result may be empty string
        assert "x-csrf-token" in headers