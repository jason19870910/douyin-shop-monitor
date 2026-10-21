"""Unit tests for Pydantic models."""

import pytest
from datetime import datetime
from pydantic import ValidationError

# Add parent directory to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models import (
    Product, Order, Creator, Video, Account,
    ComplianceRule, ComplianceLog, Media,
    AuthConfig, AlertConfig, AlertDouyinConfig, AlertDianConfig,
    ProductStatus, OrderStatus, AlertLevel,
    validate_data, validate_single, MODEL_MAP
)


class TestProductModel:
    """Test Product model."""

    def test_product_valid_minimal(self):
        """Test creating product with minimal required fields."""
        product = Product(product_id="p1", product_name="Test Product")
        assert product.product_id == "p1"
        assert product.product_name == "Test Product"
        assert product.price == 0.0
        assert product.sales_today == 0

    def test_product_valid_full(self):
        """Test creating product with all fields."""
        product = Product(
            product_id="p1",
            product_name="Test Product",
            category="Electronics",
            price=99.99,
            sales_today=10,
            sales_yesterday=5,
            inventory=100,
            conversion_rate=0.05,
            conversion_rate_today=0.06,
            conversion_rate_yesterday=0.04,
            status=ProductStatus.ON_SALE,
            fetched_at="2024-01-01T00:00:00",
        )
        assert product.price == 99.99
        assert product.status == ProductStatus.ON_SALE

    def test_product_status_enum(self):
        """Test ProductStatus enum values."""
        assert ProductStatus.ON_SALE == "on_sale"
        assert ProductStatus.OFF_SALE == "off_sale"
        assert ProductStatus.OUT_OF_STOCK == "out_of_stock"

    def test_product_extra_fields_allowed(self):
        """Test extra fields are allowed."""
        product = Product(
            product_id="p1",
            product_name="Test",
            extra_field="allowed",
            another_field=123
        )
        # Extra fields should be accessible
        assert hasattr(product, 'extra_field') or 'extra_field' in product.model_extra


class TestOrderModel:
    """Test Order model."""

    def test_order_valid_minimal(self):
        order = Order(order_id="o1")
        assert order.order_id == "o1"
        assert order.amount == 0.0
        assert order.quantity == 1

    def test_order_with_status(self):
        order = Order(
            order_id="o1",
            status=OrderStatus.WAIT_PAY,
            amount=100.0,
            create_time="2024-01-01T00:00:00"
        )
        assert order.status == OrderStatus.WAIT_PAY
        assert order.amount == 100.0

    def test_order_status_enum(self):
        """Test OrderStatus enum values."""
        assert OrderStatus.PENDING == "pending"
        assert OrderStatus.WAIT_PAY == "wait_pay"
        assert OrderStatus.DONE == "done"
        assert OrderStatus.CLOSED == "closed"


class TestCreatorModel:
    """Test Creator model."""

    def test_creator_valid(self):
        creator = Creator(creator_id="c1", creator_name="Test Creator")
        assert creator.creator_id == "c1"
        assert creator.creator_name == "Test Creator"
        assert creator.follower_count == 0

    def test_creator_full(self):
        creator = Creator(
            creator_id="c1",
            creator_name="Test Creator",
            follower_count=10000,
            following_count=100,
            video_count=50,
            total_likes=50000,
            category="Tech",
            level="L5"
        )
        assert creator.follower_count == 10000
        assert creator.category == "Tech"


class TestVideoModel:
    """Test Video model."""

    def test_video_valid(self):
        video = Video(video_id="v1", title="Test Video")
        assert video.video_id == "v1"
        assert video.title == "Test Video"
        assert video.view_count == 0

    def test_video_full(self):
        video = Video(
            video_id="v1",
            title="Test Video",
            creator_id="c1",
            creator_name="Test Creator",
            play_count=10000,  # production field name; view_count is a read-only alias
            like_count=500,
            comment_count=50,
            share_count=10,
            duration=120,
            status="published"
        )
        assert video.view_count == 10000
        assert video.duration == 120


class TestAccountModel:
    """Test Account model."""

    def test_account_valid(self):
        account = Account(account_id="a1", account_name="Test Account")
        assert account.account_id == "a1"
        assert account.account_name == "Test Account"
        assert account.platform == "douyin"

    def test_account_custom_platform(self):
        account = Account(account_id="a1", account_name="Test", platform="dian")
        assert account.platform == "dian"


class TestComplianceModels:
    """Test Compliance models."""

    def test_compliance_rule_valid(self):
        rule = ComplianceRule(
            id="r1",
            rule_name="Test Rule",
            rule_type="KEYWORD",
            rule_content={"keywords": ["test"]},
            severity="HIGH",
            category="广告法"
        )
        assert rule.id == "r1"
        assert rule.severity == "HIGH"

    def test_compliance_log_valid(self):
        log = ComplianceLog(
            id="l1",
            rule_id="r1",
            target_type="product",
            target_id="p1",
            target_name="Test Product",
            status="fail",
            details={"matched_keywords": ["test"]},
            checked_at="2024-01-01T00:00:00"
        )
        assert log.status == "fail"
        assert log.details["matched_keywords"] == ["test"]


class TestMediaModel:
    """Test Media model."""

    def test_media_valid(self):
        media = Media(
            media_id="m1",
            title="Test Media",
            type="image",
            url="https://example.com/image.jpg"
        )
        assert media.media_id == "m1"
        assert media.type == "image"


class TestAuthConfigModel:
    """Test AuthConfig model."""

    def test_auth_config_defaults(self):
        config = AuthConfig()
        assert config.authorized is False
        assert config.access_token == ""
        assert config.scope == []

    def test_auth_config_with_values(self):
        config = AuthConfig(
            douyin_app_id="app123",
            douyin_app_secret="secret456",
            authorized=True,
            access_token="token789",
            scope=["video.list", "video.create"]
        )
        assert config.douyin_app_id == "app123"
        assert config.authorized is True
        assert "video.list" in config.scope


class TestAlertConfigModels:
    """Test Alert configuration models."""

    def test_alert_config_defaults(self):
        config = AlertConfig()
        assert config.sales_drop_threshold == 0.3
        assert config.conversion_drop_threshold == 0.2
        assert config.inventory_low_threshold == 10
        assert config.enabled is True

    def test_alert_douyin_config_defaults(self):
        config = AlertDouyinConfig()
        assert config.video_view_drop_threshold == 0.3
        assert config.video_like_drop_threshold == 0.2
        assert config.creator_follower_drop_threshold == 0.1
        assert config.enabled is True

    def test_alert_dian_config_defaults(self):
        config = AlertDianConfig()
        assert config.product_sales_drop_threshold == 0.3
        assert config.order_refund_rate_threshold == 0.15
        assert config.compliance_risk_threshold == "medium"
        assert config.enabled is True


class TestValidateData:
    """Test validate_data and validate_single functions."""

    def test_validate_data_products(self):
        """Test validating product list."""
        data = [
            {"product_id": "p1", "product_name": "Product 1", "price": 100},
            {"product_id": "p2", "product_name": "Product 2", "price": 200},
        ]
        validated = validate_data(data, 'products')
        assert len(validated) == 2
        assert validated[0]['product_id'] == "p1"
        assert validated[1]['price'] == 200

    def test_validate_data_orders(self):
        """Test validating order list."""
        data = [
            {"order_id": "o1", "amount": 100.0, "status": "done"},
            {"order_id": "o2", "amount": 200.0, "status": "pending"},
        ]
        validated = validate_data(data, 'orders')
        assert len(validated) == 2
        assert validated[0]['status'] == "done"

    def test_validate_data_creators(self):
        """Test validating creator list."""
        data = [
            {"creator_id": "c1", "creator_name": "Creator 1", "follower_count": 1000},
        ]
        validated = validate_data(data, 'creators')
        assert len(validated) == 1
        assert validated[0]['follower_count'] == 1000

    def test_validate_data_unknown_type(self):
        """Test validating unknown type returns original data."""
        data = [{"custom": "data"}]
        validated = validate_data(data, 'unknown_type')
        assert validated == data

    def test_validate_single_valid(self):
        """Test validating single item."""
        data = {"product_id": "p1", "product_name": "Test", "price": 99.99}
        validated = validate_single(data, 'products')
        assert validated['product_id'] == "p1"
        assert validated['price'] == 99.99

    def test_validate_single_invalid_keeps_original(self):
        """Test that validation error keeps original data."""
        # Missing required field product_id
        data = {"product_name": "Test"}
        validated = validate_single(data, 'products')
        # Should keep original since validation fails
        assert validated == data

    def test_validate_data_invalid_item_kept(self):
        """Test that invalid items in list are kept as-is."""
        data = [
            {"product_id": "p1", "product_name": "Valid"},
            {"product_name": "Missing ID"},  # Invalid - missing product_id
        ]
        validated = validate_data(data, 'products')
        assert len(validated) == 2
        assert validated[0]['product_id'] == "p1"
        # Invalid item should be kept as-is
        assert validated[1] == {"product_name": "Missing ID"}


class TestModelMap:
    """Test MODEL_MAP completeness."""

    def test_model_map_contains_all_expected_types(self):
        expected_types = {
            'products', 'orders', 'creators', 'videos', 'accounts',
            'compliance_rules', 'compliance_logs', 'media', 'auth',
            'alert_config', 'alert_douyin_config', 'alert_dian_config'
        }
        assert set(MODEL_MAP.keys()) == expected_types

    def test_model_map_values_are_classes(self):
        for model_class in MODEL_MAP.values():
            assert isinstance(model_class, type)


class TestEnums:
    """Test enum definitions."""

    def test_product_status_values(self):
        assert set(ProductStatus.__members__.keys()) == {
            'ON_SALE', 'OFF_SALE', 'OUT_OF_STOCK'
        }

    def test_order_status_values(self):
        expected = {
            'PENDING', 'WAIT_PAY', 'WAIT_SEND', 'SENT', 'DONE',
            'CLOSED', 'AFTER_SALE', 'ABNORMAL', 'TIMEOUT_SEND',
            'URGENT_SEND', 'COMPLETED', 'SHIPPED'
        }
        assert set(OrderStatus.__members__.keys()) == expected

    def test_alert_level_values(self):
        assert set(AlertLevel.__members__.keys()) == {
            'INFO', 'WARNING', 'ERROR', 'CRITICAL'
        }


if __name__ == "__main__":
    pytest.main([__file__, "-v"])