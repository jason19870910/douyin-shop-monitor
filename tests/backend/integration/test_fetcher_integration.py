"""Integration tests for fetcher with mocked external APIs."""

import pytest
import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.fetcher import (
    _fetch_products_from_api,
    _fetch_orders_from_api,
    _fetch_creators_from_api,
    _fetch_creator_works_from_api,
    fetch_and_store_products,
    fetch_and_store_orders,
    fetch_and_store_creators,
    fetch_and_store_creator_works,
    fetch_and_check_compliance,
    check_alerts,
    scheduled_job,
    get_fxg_cookies,
    get_creator_cookies,
    parse_cookies,
)
from services.fetcher import cache, CACHE_KEYS


def _alert_cache_get(products):
    """Build a cache.get side_effect for alert tests.

    check_alerts runs three independent groups; the douyin/dian groups read
    their own config keys, so those must be explicitly disabled here to keep
    these tests focused on the general (product) alert logic.
    """
    def _get(key, default=None):
        if key == CACHE_KEYS['products']:
            return products
        if key in (CACHE_KEYS['alert_douyin_config'], CACHE_KEYS['alert_dian_config']):
            return {'enabled': False}
        return default
    return _get


class TestFetchProductsIntegration:
    """Integration tests for product fetching."""

    @patch('services.fetcher.requests.get')
    @patch('services.fetcher._read_secret')
    @patch('services.fetcher.get_fxg_cookies')
    def test_fetch_products_success(self, mock_cookies, mock_read_secret, mock_get):
        """Test successful product fetch from API."""
        # Setup mocks (sign_request is imported lazily inside _request only)
        mock_cookies.return_value = {"session": "test"}
        mock_read_secret.side_effect = lambda *args, **kwargs: {
            '__TOKEN': 'token123',
            'MS_TOKEN': 'ms456',
            'verifyFp': 'verify789',
            'fp': 'fp101',
        }.get(args[1] if len(args) > 1 else args[0], '')

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "products": [
                    {"product_id": "p1", "product_name": "Product 1", "price": 100},
                    {"product_id": "p2", "product_name": "Product 2", "price": 200},
                ]
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = _fetch_products_from_api()

        assert len(result) == 2
        assert result[0]['product_id'] == 'p1'
        assert result[1]['product_name'] == 'Product 2'
        mock_get.assert_called_once()

    @patch('services.fetcher.requests.get')
    @patch('services.fetcher._read_secret')
    @patch('services.fetcher.get_fxg_cookies')
    def test_fetch_products_api_error(self, mock_cookies, mock_read_secret, mock_get):
        """Test product fetch handles API errors."""
        mock_cookies.return_value = {"session": "test"}
        mock_read_secret.return_value = "token"

        mock_get.side_effect = Exception("Connection error")

        with pytest.raises(Exception):
            _fetch_products_from_api()

    @patch('services.fetcher._fetch_products_from_api')
    @patch('services.fetcher.cache')
    @patch('services.fetcher.save_json_file')
    def test_fetch_and_store_products(self, mock_save, mock_cache, mock_fetch):
        """Test fetch and store products end-to-end."""
        mock_fetch.return_value = [
            {"product_id": "p1", "product_name": "Product 1", "price": 100}
        ]
        
        result = fetch_and_store_products()

        assert result['status'] == 'success'
        assert result['count'] == 1
        mock_cache.set.assert_called_once()
        mock_save.assert_called_once()


class TestFetchOrdersIntegration:
    """Integration tests for order fetching."""

    @patch('services.fetcher.requests.get')
    @patch('services.fetcher.get_fxg_cookies')
    def test_fetch_orders_success(self, mock_cookies, mock_get):
        """Test successful order fetch from API."""
        mock_cookies.return_value = {"session": "test"}
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "orders": [
                    {"order_id": "o1", "amount": 100, "status": "done"},
                    {"order_id": "o2", "amount": 200, "status": "pending"},
                ]
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = _fetch_orders_from_api()

        assert len(result) == 2
        assert result[0]['order_id'] == 'o1'
        assert result[1]['amount'] == 200

    @patch('services.fetcher._fetch_orders_from_api')
    @patch('services.fetcher.cache')
    @patch('services.fetcher.save_json_file')
    def test_fetch_and_store_orders(self, mock_save, mock_cache, mock_fetch):
        """Test fetch and store orders end-to-end."""
        mock_fetch.return_value = [
            {"order_id": "o1", "amount": 100, "status": "done"}
        ]
        
        result = fetch_and_store_orders()

        assert result['status'] == 'success'
        assert result['count'] == 1


class TestFetchCreatorsIntegration:
    """Integration tests for creator fetching."""

    @patch('services.fetcher.requests.post')
    @patch('services.fetcher.get_creator_cookies')
    def test_fetch_creators_success(self, mock_cookies, mock_post):
        """Test successful creator fetch from API."""
        mock_cookies.return_value = {"session": "test"}
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "creators": [
                    {"creator_id": "c1", "creator_name": "Creator 1", "follower_count": 1000},
                    {"creator_id": "c2", "creator_name": "Creator 2", "follower_count": 2000},
                ]
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = _fetch_creators_from_api()

        assert len(result) == 2
        assert result[0]['creator_id'] == 'c1'
        assert result[1]['follower_count'] == 2000

    @patch('services.fetcher._fetch_creators_from_api')
    @patch('services.fetcher.cache')
    @patch('services.fetcher.save_json_file')
    def test_fetch_and_store_creators(self, mock_save, mock_cache, mock_fetch):
        """Test fetch and store creators end-to-end."""
        mock_fetch.return_value = [
            {"creator_id": "c1", "creator_name": "Creator 1", "follower_count": 1000}
        ]
        
        result = fetch_and_store_creators()

        assert result['status'] == 'success'
        assert result['count'] == 1


class TestFetchCreatorWorksIntegration:
    """Integration tests for creator works fetching."""

    @patch('services.fetcher.requests.get')
    @patch('services.fetcher.get_creator_cookies')
    def test_fetch_creator_works_success(self, mock_cookies, mock_get):
        """Test successful creator works fetch."""
        mock_cookies.return_value = {"session": "test"}

        mock_response = MagicMock()
        # Production parser reads aweme_list / items at the top level
        mock_response.json.return_value = {
            "aweme_list": [
                {"work_id": "w1", "title": "Work 1", "status": "published"},
                {"work_id": "w2", "title": "Work 2", "status": "draft"},
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = _fetch_creator_works_from_api()

        assert len(result) == 2
        assert result[0]['work_id'] == 'w1'

    @patch('services.fetcher._fetch_creator_works_from_api')
    @patch('services.fetcher.cache')
    @patch('services.fetcher.save_json_file')
    def test_fetch_and_store_creator_works(self, mock_save, mock_cache, mock_fetch):
        """Test fetch and store creator works end-to-end."""
        mock_fetch.return_value = [
            {"work_id": "w1", "title": "Work 1"}
        ]
        
        result = fetch_and_store_creator_works()

        assert result['status'] == 'success'
        assert result['count'] == 1


class TestComplianceCheckIntegration:
    """Integration tests for compliance checking."""

    @patch('services.fetcher._fetch_products_from_api')
    def test_fetch_and_check_compliance(self, mock_fetch_products):
        """Test compliance check runs."""
        # No cached products and empty API result -> graceful no-op success
        mock_fetch_products.return_value = []

        result = fetch_and_check_compliance()
        assert result['status'] == 'success'
        assert 'message' in result


class TestAlertCheckingIntegration:
    """Integration tests for alert checking."""

    @patch('services.fetcher.cache')
    @patch('services.fetcher.get_alert_config')
    @patch('services.fetcher.send_alert_notification')
    def test_check_alerts_no_products(self, mock_send_alert, mock_get_config, mock_cache):
        """Test alert check with no products."""
        mock_cache.get.side_effect = _alert_cache_get([])
        mock_get_config.return_value = {
            'sales_drop_threshold': 0.3,
            'conversion_drop_threshold': 0.2,
            'inventory_low_threshold': 10,
            'enabled': True
        }

        result = check_alerts()

        assert result['status'] == 'success'
        assert result['alerts_triggered'] == 0
        mock_send_alert.assert_not_called()

    @patch('services.fetcher.cache')
    @patch('services.fetcher.get_alert_config')
    @patch('services.fetcher.send_alert_notification')
    def test_check_alerts_sales_drop(self, mock_send_alert, mock_get_config, mock_cache):
        """Test alert check triggers on sales drop."""
        mock_cache.get.side_effect = _alert_cache_get([
            {
                'product_id': 'p1',
                'product_name': 'Test Product',
                'sales_today': 10,
                'sales_yesterday': 100,
                'inventory': 50,
                'conversion_rate_today': 0.05,
                'conversion_rate_yesterday': 0.05,
            }
        ])
        mock_get_config.return_value = {
            'sales_drop_threshold': 0.3,
            'conversion_drop_threshold': 0.2,
            'inventory_low_threshold': 10,
            'notification_email': 'test@example.com',
            'enabled': True
        }

        result = check_alerts()

        assert result['status'] == 'success'
        assert result['alerts_triggered'] == 1
        mock_send_alert.assert_called_once()

    @patch('services.fetcher.cache')
    @patch('services.fetcher.get_alert_config')
    @patch('services.fetcher.send_alert_notification')
    def test_check_alerts_low_inventory(self, mock_send_alert, mock_get_config, mock_cache):
        """Test alert check triggers on low inventory."""
        mock_cache.get.side_effect = _alert_cache_get([
            {
                'product_id': 'p1',
                'product_name': 'Test Product',
                'sales_today': 50,
                'sales_yesterday': 50,
                'inventory': 5,  # Below threshold of 10
                'conversion_rate_today': 0.05,
                'conversion_rate_yesterday': 0.05,
            }
        ])
        mock_get_config.return_value = {
            'sales_drop_threshold': 0.3,
            'conversion_drop_threshold': 0.2,
            'inventory_low_threshold': 10,
            'notification_email': 'test@example.com',
            'enabled': True
        }

        result = check_alerts()

        assert result['status'] == 'success'
        assert result['alerts_triggered'] == 1
        mock_send_alert.assert_called_once()

    @patch('services.fetcher.cache')
    @patch('services.fetcher.get_alert_config')
    @patch('services.fetcher.send_alert_notification')
    def test_check_alerts_conversion_drop(self, mock_send_alert, mock_get_config, mock_cache):
        """Test alert check triggers on conversion rate drop."""
        mock_cache.get.side_effect = _alert_cache_get([
            {
                'product_id': 'p1',
                'product_name': 'Test Product',
                'sales_today': 50,
                'sales_yesterday': 50,
                'inventory': 50,
                'conversion_rate_today': 0.01,  # Big drop from 0.05
                'conversion_rate_yesterday': 0.05,
            }
        ])
        mock_get_config.return_value = {
            'sales_drop_threshold': 0.3,
            'conversion_drop_threshold': 0.2,
            'inventory_low_threshold': 10,
            'notification_email': 'test@example.com',
            'enabled': True
        }

        result = check_alerts()

        assert result['status'] == 'success'
        assert result['alerts_triggered'] == 1
        mock_send_alert.assert_called_once()

    @patch('services.fetcher.cache')
    @patch('services.fetcher.get_alert_config')
    def test_check_alerts_disabled(self, mock_get_config, mock_cache):
        """Test alert check skipped when disabled."""
        mock_get_config.return_value = {'enabled': False}
        mock_cache.get.side_effect = _alert_cache_get([])

        result = check_alerts()

        assert result['status'] == 'skipped'
        assert result['reason'] == 'all alert groups disabled'


class TestScheduledJobIntegration:
    """Integration tests for scheduled job."""

    @patch('services.fetcher.fetch_and_store_products')
    @patch('services.fetcher.fetch_and_store_orders')
    @patch('services.fetcher.fetch_and_store_creators')
    @patch('services.fetcher.fetch_and_store_creator_works')
    @patch('services.fetcher.fetch_and_check_compliance')
    @patch('services.fetcher.check_alerts')
    @patch('services.fetcher.cache')
    def test_scheduled_job_calls_all_tasks(self, mock_cache, mock_alerts, mock_compliance,
                                             mock_creator_works, mock_creators, mock_orders, mock_products):
        """Test scheduled job calls all fetch tasks."""
        mock_products.return_value = {'status': 'success', 'count': 10}
        mock_orders.return_value = {'status': 'success', 'count': 5}
        mock_creators.return_value = {'status': 'success', 'count': 3}
        mock_creator_works.return_value = {'status': 'success', 'count': 2}
        mock_compliance.return_value = {'status': 'success'}
        mock_alerts.return_value = {'status': 'success', 'alerts_triggered': 0}

        result = scheduled_job()

        # scheduled_job nests per-task results under 'results' alongside status/duration_ms
        assert 'products' in result['results']
        assert 'orders' in result['results']
        assert 'creators' in result['results']
        assert 'creator_works' in result['results']
        assert 'compliance' in result['results']
        assert 'alerts' in result['results']
        mock_products.assert_called_once()
        mock_orders.assert_called_once()
        mock_creators.assert_called_once()
        mock_compliance.assert_called_once()
        mock_alerts.assert_called_once()


class TestCookieParsingIntegration:
    """Integration tests for cookie parsing."""

    def test_parse_cookies_realistic(self):
        """Test parsing realistic cookie string."""
        cookie = (
            "sessionid=abc123; "
            "csrf_token=xyz789; "
            "user_pref=dark_mode; "
            "tracking_id=trk_12345"
        )
        result = parse_cookies(cookie)
        assert result['sessionid'] == 'abc123'
        assert result['csrf_token'] == 'xyz789'
        assert result['user_pref'] == 'dark_mode'
        assert result['tracking_id'] == 'trk_12345'

    def test_parse_cookies_with_encoded_values(self):
        """Test parsing cookies with URL-encoded values."""
        cookie = "token=abc%3D123; session=xyz%2F456"
        result = parse_cookies(cookie)
        assert result['token'] == 'abc%3D123'
        assert result['session'] == 'xyz%2F456'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])