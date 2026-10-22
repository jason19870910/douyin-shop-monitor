"""Unit tests for orders.field normalization (抖店原始字段 → 平台标准字段)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.order_normalizer import (
    map_order_status,
    normalize_order,
    normalize_orders,
)

# 取自线上 Redis (douyin:monitor:orders) 的真实抖店订单关键字段
FXG_RAW_ORDER = {
    'order_id': '',
    'shop_order_id': '6952528259545240685',
    'order_status': 4,
    'order_status_info': {'order_status_text': '已关闭'},
    'pay_amount': 6202,
    'total_price': 6202,
    'total_product_count': 1,
    'product_count': 1,
    'create_time': 1777760073,
    'pay_time': 1777760077,
    'user_nickname': '东*',
    'product_item': [
        {
            'item_order_id': '6952528259545240685',
            'product_id': '3817267156467450214',
            'product_name': '海盐嘭润保湿沐浴露紧致嫩肤补水留香沐浴乳',
            'total_amount': 6202,
            'pay_amount': 6202,
            'combo_num': 1,
        }
    ],
    'fetched_at': '2026-10-22T02:48:43.141802',
}

MOCK_PLATFORM_ORDER = {
    'order_id': 'mock_o_001',
    'product_name': '模拟商品-爆款T恤',
    'product_id': 'mock_p_001',
    'amount': 99.9,
    'status': 'completed',
    'create_time': '2026-10-22T00:00:00',
    'quantity': 1,
    'fetched_at': '2026-10-22T00:00:00',
}


class TestNormalizeOrder:
    def test_fxg_raw_order_is_normalized(self):
        o = normalize_order(FXG_RAW_ORDER)
        assert o['order_id'] == '6952528259545240685'
        assert o['product_name'] == '海盐嘭润保湿沐浴露紧致嫩肤补水留香沐浴乳'
        assert o['product_id'] == '3817267156467450214'
        assert o['pay_amount'] == 62.02
        assert o['amount'] == 62.02
        assert o['quantity'] == 1
        assert o['status'] == 'cancelled'
        assert o['buyer_nickname'] == '东*'

    def test_unix_seconds_converted_to_iso_with_timezone(self):
        o = normalize_order(FXG_RAW_ORDER)
        assert o['create_time'] == '2026-05-03T06:14:33+08:00'
        assert o['pay_time'] == '2026-05-03T06:14:37+08:00'

    def test_raw_order_is_not_mutated(self):
        normalize_order(FXG_RAW_ORDER)
        assert FXG_RAW_ORDER['order_id'] == ''
        assert FXG_RAW_ORDER['create_time'] == 1777760073

    def test_platform_shaped_order_passes_through_unchanged(self):
        o = normalize_order(dict(MOCK_PLATFORM_ORDER))
        assert o == MOCK_PLATFORM_ORDER

    def test_already_normalized_order_is_idempotent(self):
        once = normalize_order(FXG_RAW_ORDER)
        twice = normalize_order(once)
        assert twice == once

    def test_missing_optional_fields_do_not_break(self):
        o = normalize_order({'shop_order_id': 'x1'})
        assert o['order_id'] == 'x1'
        assert 'pay_amount' not in o
        assert o['status'] == 'unknown'

    def test_non_dict_passthrough(self):
        assert normalize_order(None) is None
        assert normalize_order('bad') == 'bad'


class TestMapOrderStatus:
    def test_status_text_direct_mapping(self):
        assert map_order_status({'order_status_info': {'order_status_text': '已发货'}}) == 'shipped'
        assert map_order_status({'order_status_info': {'order_status_text': '已关闭'}}) == 'cancelled'

    def test_status_keyword_fallback(self):
        assert map_order_status({'order_status_info': {'order_status_text': '部分退款中'}}) == 'refunded'

    def test_numeric_code_fallback(self):
        assert map_order_status({'order_status': 4}) == 'cancelled'
        assert map_order_status({'order_status': 3}) == 'shipped'
        assert map_order_status({'order_status': 99}) == 'unknown'

    def test_empty_order(self):
        assert map_order_status({}) == 'unknown'


class TestNormalizeOrders:
    def test_list_normalization(self):
        result = normalize_orders([FXG_RAW_ORDER, MOCK_PLATFORM_ORDER])
        assert result[0]['order_id'] == '6952528259545240685'
        assert result[1] == MOCK_PLATFORM_ORDER

    def test_non_list_passthrough(self):
        assert normalize_orders(None) is None
        assert normalize_orders({'a': 1}) == {'a': 1}
