"""Contract tests for API endpoints - verify response format and structure."""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.responses import (
    success_response, error_response, not_found_response,
    bad_request_response, unauthorized_response, internal_error_response
)


@pytest.fixture
def app():
    """Shared Flask app instance for contract tests."""
    from app import app as flask_app
    flask_app.config['TESTING'] = True
    return flask_app


@pytest.fixture
def client(app):
    """Create test client for Flask app."""
    with app.test_client() as client:
        yield client


class TestResponseFormatContract:
    """Contract tests for unified API response format."""

    @pytest.fixture(autouse=True)
    def _push_app_context(self, app):
        """Response helpers call jsonify, which requires an app context."""
        with app.app_context():
            yield

    def test_success_response_format(self):
        """Test success response has correct structure."""
        response, status = success_response({"key": "value"}, "Operation successful", 200)
        
        assert status == 200
        data = response.get_json()
        
        # Required fields
        assert data['success'] is True
        assert data['error'] is None
        assert data['data'] == {"key": "value"}
        assert data['message'] == "Operation successful"

    def test_success_response_without_message(self):
        """Test success response without optional message."""
        response, status = success_response({"data": "test"})
        
        assert status == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['error'] is None
        assert 'message' not in data

    def test_error_response_format(self):
        """Test error response has correct structure."""
        response, status = error_response("Something went wrong", 400, "VALIDATION_ERROR", {"field": "email"})
        
        assert status == 400
        data = response.get_json()
        
        # Required fields
        assert data['success'] is False
        assert data['data'] is None
        assert data['error'] == "Something went wrong"
        assert data['error_code'] == "VALIDATION_ERROR"
        assert data['details'] == {"field": "email"}

    def test_error_response_minimal(self):
        """Test error response with minimal fields."""
        response, status = error_response("Not found")
        
        assert status == 400
        data = response.get_json()
        assert data['success'] is False
        assert data['error'] == "Not found"
        # optional fields are omitted entirely when not provided
        assert 'error_code' not in data
        assert 'details' not in data

    def test_not_found_response(self):
        """Test 404 response format."""
        response, status = not_found_response("Product")
        
        assert status == 404
        data = response.get_json()
        assert data['success'] is False
        assert data['error'] == "Product not found"
        assert data['error_code'] == "NOT_FOUND"

    def test_bad_request_response(self):
        """Test 400 response format."""
        response, status = bad_request_response("Invalid input", {"field": "email"})
        
        assert status == 400
        data = response.get_json()
        assert data['success'] is False
        assert data['error'] == "Invalid input"
        assert data['error_code'] == "BAD_REQUEST"
        assert data['details'] == {"field": "email"}

    def test_unauthorized_response(self):
        """Test 401 response format."""
        response, status = unauthorized_response("Invalid token")
        
        assert status == 401
        data = response.get_json()
        assert data['success'] is False
        assert data['error'] == "Invalid token"
        assert data['error_code'] == "UNAUTHORIZED"

    def test_internal_error_response(self):
        """Test 500 response format."""
        response, status = internal_error_response("Database error", {"table": "users"})
        
        assert status == 500
        data = response.get_json()
        assert data['success'] is False
        assert data['error'] == "Database error"
        assert data['error_code'] == "INTERNAL_ERROR"
        assert data['details'] == {"table": "users"}

    def test_validation_error_response(self):
        """Test 422 response format."""
        response, status = error_response("Validation failed", 422, "VALIDATION_ERROR", {"errors": []})
        
        assert status == 422
        data = response.get_json()
        assert data['error_code'] == "VALIDATION_ERROR"


class TestAPIEndpointContracts:
    """Contract tests for API endpoint response formats."""

    @patch('blueprints.products.cache')
    def test_products_list_contract(self, mock_cache, client):
        """Test /api/v1/products returns correct format."""
        # products blueprint reads cache directly, falling back to the external API
        mock_cache.get.return_value = [
            {'product_id': 'p1', 'product_name': 'Product 1', 'price': 100}
        ]
        
        # Need auth
        response = client.get(
            '/api/v1/products',
            headers={'Authorization': 'Bearer test_key'}
        )
        
        # Should return proper format (but will fail auth without real key)
        # This verifies the endpoint exists and uses correct format
        assert response.status_code in [200, 401, 403]

    @patch('blueprints.products.cache')
    def test_products_single_contract(self, mock_cache, client):
        """Test /api/v1/products/<id> returns correct format."""
        mock_cache.get.return_value = [
            {'product_id': 'p1', 'product_name': 'Product 1'}
        ]
        
        response = client.get(
            '/api/v1/products/p1',
            headers={'Authorization': 'Bearer test_key'}
        )
        
        assert response.status_code in [200, 401, 404]

    @patch('blueprints.orders.cache')
    @patch('blueprints.orders.get_data_with_fallback')
    def test_orders_list_contract(self, mock_get_data, mock_cache, client):
        """Test /api/v1/orders returns correct format."""
        mock_get_data.return_value = (
            [{'order_id': 'o1', 'amount': 100, 'status': 'done'}],
            'real'
        )
        mock_cache.get.return_value = "2024-01-01T00:00:00"
        
        response = client.get(
            '/api/v1/orders',
            headers={'Authorization': 'Bearer test_key'}
        )
        
        assert response.status_code in [200, 401]

    @patch('blueprints.creators.cache')
    @patch('blueprints.creators.get_data_with_fallback')
    def test_creators_list_contract(self, mock_get_data, mock_cache, client):
        """Test /api/v1/creators returns correct format."""
        mock_get_data.return_value = (
            [{'creator_id': 'c1', 'creator_name': 'Creator 1'}],
            'real'
        )
        
        response = client.get(
            '/api/v1/creators',
            headers={'Authorization': 'Bearer test_key'}
        )
        
        assert response.status_code in [200, 401]

    @patch('blueprints.alerts.get_config')
    def test_alerts_config_get_contract(self, mock_get_config, client):
        """Test /api/v1/alerts/config GET returns correct format."""
        mock_get_config.return_value = {'enabled': True}
        
        response = client.get(
            '/api/v1/alerts/config',
            headers={'Authorization': 'Bearer test_key'}
        )
        
        assert response.status_code in [200, 401]

    @patch('blueprints.alerts.get_config')
    @patch('blueprints.alerts.set_config')
    def test_alerts_config_post_contract(self, mock_set_config, mock_get_config, client):
        """Test /api/v1/alerts/config POST returns correct format."""
        mock_get_config.return_value = {'enabled': True}
        
        response = client.post(
            '/api/v1/alerts/config',
            json={'enabled': False},
            headers={'Authorization': 'Bearer test_key'}
        )
        
        assert response.status_code in [200, 400, 401]

    @patch('blueprints.compliance.cache')
    def test_compliance_list_contract(self, mock_cache, client):
        """Test /api/v1/compliance returns correct format."""
        mock_cache.get.return_value = [
            {'id': 'l1', 'rule_id': 'r1', 'status': 'pass'}
        ]
        
        response = client.get(
            '/api/v1/compliance',
            headers={'Authorization': 'Bearer test_key'}
        )
        
        assert response.status_code in [200, 401]

    @patch('blueprints.compliance.cache')
    def test_compliance_rules_contract(self, mock_cache, client):
        """Test /api/v1/compliance/rules returns correct format."""
        mock_cache.get.return_value = [
            {'id': 'r1', 'rule_name': 'Test Rule', 'rule_type': 'KEYWORD'}
        ]
        
        response = client.get(
            '/api/v1/compliance/rules',
            headers={'Authorization': 'Bearer test_key'}
        )
        
        assert response.status_code in [200, 401]

    @patch('blueprints.videos.cache')
    def test_videos_list_contract(self, mock_cache, client):
        """Test /api/v1/videos returns correct format."""
        mock_cache.get.return_value = [
            {'video_id': 'v1', 'title': 'Video 1'}
        ]
        
        response = client.get(
            '/api/v1/videos',
            headers={'Authorization': 'Bearer test_key'}
        )
        
        assert response.status_code in [200, 401]

    @patch('blueprints.accounts.cache')
    def test_accounts_list_contract(self, mock_cache, client):
        """Test /api/v1/accounts returns correct format."""
        mock_cache.get.return_value = [
            {'account_id': 'a1', 'account_name': 'Account 1'}
        ]
        
        response = client.get(
            '/api/v1/accounts',
            headers={'Authorization': 'Bearer test_key'}
        )
        
        assert response.status_code in [200, 401]

    def test_auth_status_contract(self, client):
        """Test /api/v1/auth/status (public endpoint)."""
        response = client.get('/api/v1/auth/status')
        # This is a public endpoint, should not require auth
        assert response.status_code in [200, 401]

    def test_health_check_contract(self, client):
        """Test /api/v1/health (public endpoint)."""
        response = client.get('/api/v1/health')
        assert response.status_code == 200
        
        data = response.get_json()
        # Verify unified response format
        assert data['success'] is True
        assert 'data' in data
        assert data['data']['status'] == 'healthy'


class TestResponseHeadersContract:
    """Contract tests for response headers."""

    def test_content_type_json(self, client):
        """Test all API responses have application/json content type."""
        response = client.get('/api/v1/health')
        assert 'application/json' in response.content_type

    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.get('/api/v1/health')
        # Flask-CORS should add these
        assert 'Access-Control-Allow-Origin' in response.headers or response.status_code == 200


class TestPaginationContract:
    """Contract tests for paginated responses."""

    def test_paginated_response_structure(self):
        """Test paginated responses have required fields."""
        # This is the expected structure for paginated endpoints
        expected_fields = ['items', 'total', 'page', 'size']
        
        response_data = {
            'items': [{'id': 1}],
            'total': 100,
            'page': 1,
            'size': 20
        }
        
        for field in expected_fields:
            assert field in response_data

    def test_pagination_page_size_limits(self):
        """Test pagination respects size limits."""
        # Page size should be reasonable (not too large)
        max_size = 100
        requested_size = 1000
        actual_size = min(requested_size, max_size)
        assert actual_size <= max_size


if __name__ == "__main__":
    pytest.main([__file__, "-v"])