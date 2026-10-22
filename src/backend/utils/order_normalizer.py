"""抖店订单原始字段 → 平台标准字段归一化。

fetcher 同步落库的是抖店 fxg 订单详情原始 JSON，与前端 Order 类型
（src/frontend/src/api/index.ts）字段名、单位、时基均不一致，直接下发
会导致订单表格渲染为空值（order_id 空串、pay_amount 为分、create_time
为 Unix 秒等）。本模块在 API 输出层做字段映射，保持 Redis 中的原始
数据不动。

对已经是平台字段的数据（mock / 已归一化数据）原样返回，保证幂等。
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

# 抖店 fxg 订单状态文案 → 平台标准状态（与前端 orderStatus.ts 取值一致）
_STATUS_TEXT_MAP = {
    '待付款': 'pending',
    '待支付': 'pending',
    '备货中': 'pending',
    '已支付': 'pending',
    '待发货': 'pending',
    '已发货': 'shipped',
    '派送中': 'shipped',
    '已签收': 'completed',
    '已完成': 'completed',
    '已取消': 'cancelled',
    '已关闭': 'cancelled',
    '退款中': 'refunded',
    '退款成功': 'refunded',
    '已退款': 'refunded',
    '售后中': 'refunded',
}

_STATUS_KEYWORDS = (
    ('退款', 'refunded'),
    ('退货', 'refunded'),
    ('取消', 'cancelled'),
    ('关闭', 'cancelled'),
    ('发货', 'shipped'),
    ('派送', 'shipped'),
    ('送达', 'shipped'),
    ('签收', 'completed'),
    ('完成', 'completed'),
    ('支付', 'pending'),
    ('付款', 'pending'),
)

# fxg 数值状态码兜底映射（线上实测 order_status=4 对应文案"已关闭"）
_STATUS_CODE_MAP = {
    1: 'pending',   # 待支付
    2: 'pending',   # 已支付/待发货
    3: 'shipped',   # 已发货
    4: 'cancelled', # 已关闭（实测）
    5: 'cancelled', # 已取消
    6: 'cancelled', # 关闭
    7: 'refunded',  # 售后/退款
}

_CN_TZ = timezone(timedelta(hours=8), name='Asia/Shanghai')

# fxg 原始订单专有字段（用于识别未归一化数据；mock 平台字段无这些键）
_FXG_MARKERS = ('shop_order_id', 'product_item', 'order_status_info', 'total_product_count')


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _unix_to_iso(ts: Any) -> Optional[str]:
    """Unix 秒 → 带东八区时区的 ISO8601 字符串；非法值返回 None。"""
    if not _is_number(ts) or ts <= 0:
        return None
    try:
        return datetime.fromtimestamp(ts, tz=_CN_TZ).isoformat(timespec='seconds')
    except (OverflowError, OSError, ValueError):
        return None


def map_order_status(raw: Dict[str, Any]) -> str:
    """把抖店订单状态映射为平台标准状态。

    优先使用 order_status_info.order_status_text 文案；
    文案缺失时回退数值码 order_status；都不可识别时返回 'unknown'。
    """
    text = ''
    info = raw.get('order_status_info')
    if isinstance(info, dict):
        text = str(info.get('order_status_text') or '')
    if not text and raw.get('order_status_text'):
        text = str(raw['order_status_text'])

    if text:
        if text in _STATUS_TEXT_MAP:
            return _STATUS_TEXT_MAP[text]
        for keyword, mapped in _STATUS_KEYWORDS:
            if keyword in text:
                return mapped

    code = raw.get('order_status')
    if _is_number(code):
        return _STATUS_CODE_MAP.get(int(code), 'unknown')

    return 'unknown'


def _first_product_item(raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    for key in ('product_item', 'item_list', 'sku_list'):
        items = raw.get(key)
        if isinstance(items, list) and items and isinstance(items[0], dict):
            return items[0]
    return None


def normalize_order(raw: Any) -> Any:
    """把抖店原始订单映射为前端 Order 字段；已是平台字段的原样返回。"""
    if not isinstance(raw, dict):
        return raw
    if not any(marker in raw for marker in _FXG_MARKERS):
        # mock 数据或已归一化数据，保持幂等
        return raw
    if isinstance(raw.get('create_time'), str):
        # 已归一化：create_time 已为 ISO 字符串，二次调用不再处理（金额避免重复分→元）
        return raw

    o = dict(raw)

    # 订单号：fxg 的 order_id 常为空串，真单号在 shop_order_id
    order_id = raw.get('shop_order_id') or raw.get('order_id') or raw.get('order_id_for_show')
    if order_id:
        o['order_id'] = str(order_id)

    # 商品信息：取 product_item[0]
    item = _first_product_item(raw)
    if item:
        if item.get('product_name'):
            o['product_name'] = str(item['product_name'])
        if item.get('product_id'):
            o['product_id'] = str(item['product_id'])

    # 金额：单位分 → 元（fxg 金额字段一律为分，见 /orders/stats 同款处理）
    pay = raw.get('pay_amount', raw.get('total_price'))
    if _is_number(pay) and pay:
        yuan = round(pay / 100, 2)
        o['pay_amount'] = yuan
        o['amount'] = yuan

    # 数量
    qty = raw.get('total_product_count', raw.get('product_count'))
    if _is_number(qty):
        o['quantity'] = int(qty)

    # 状态
    o['status'] = map_order_status(raw)

    # 时间：Unix 秒 → ISO8601（同时兼容 start_date/end_date 的字符串过滤）
    for key in ('create_time', 'update_time', 'pay_time', 'ship_time', 'exp_ship_time'):
        iso = _unix_to_iso(raw.get(key))
        if iso:
            o[key] = iso

    # 买家昵称（前端创作者列回退链 buyer_nickname）
    if raw.get('user_nickname'):
        o['buyer_nickname'] = str(raw['user_nickname'])

    return o


def normalize_orders(raw_orders: Any) -> Any:
    """对订单列表批量归一化；非列表原样返回。"""
    if not isinstance(raw_orders, list):
        return raw_orders
    return [normalize_order(o) for o in raw_orders]
