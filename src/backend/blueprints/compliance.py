"""Compliance blueprint."""
import logging
import os

from flask import Blueprint, request
from services.rule_engine import get_rule_engine, run_compliance_check, CheckResult, RuleContext
from services.fetcher import (
    cache, CACHE_KEYS, DEFAULT_COMPLIANCE,
    COMPLIANCE_RULES_FILE, COMPLIANCE_FILE, COMPLIANCE_LOG_STATUSES,
    filter_rules_for_target, build_compliance_log_entry,
    _enrich_product_with_haohuo, _append_compliance_logs, _persist_compliance_logs,
    ensure_haohuo_rules,
)
from datetime import datetime
from utils.responses import success_response, not_found_response, bad_request_response

logger = logging.getLogger(__name__)

compliance_bp = Blueprint('compliance', __name__, url_prefix='/api/v1')

ALLOWED_RULE_TYPES = {
    'KEYWORD', 'REGEX', 'PRICE', 'LICENSE', 'ML_MODEL', 'CUSTOM_SCRIPT',
    # Haohuo (好货) 预览数据专用规则类型
    'HAOHUO_IMAGE', 'HAOHUO_SPEC', 'HAOHUO_PRICE', 'HAOHUO_FATAL'
}
ALLOWED_SEVERITIES = {'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'}


def _parse_page(value, default, *, minimum=1, maximum=1000):
    """Safely parse paginated query parameters."""
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    if parsed < minimum:
        return minimum
    if parsed > maximum:
        return maximum
    return parsed


def _ensure_list(value):
    """Guarantee a list value for cached compliance data."""
    if not isinstance(value, list):
        return []
    return value

# 旧违规日志 category/target_type 为英文枚举，读取展示时统一归一化为中文标签
CATEGORY_LABELS = {
    'product': '商品合规',
    'haohuo_product': '商品合规',
    'work': '作品合规',
    'video': '作品合规',
}


def _normalize_category(log):
    """归一化违规记录分类：缺失时回退 target_type，英文枚举映射为中文。"""
    cat = str(log.get('category') or '').strip()
    if not cat:
        cat = str(log.get('target_type') or '').strip()
    return CATEGORY_LABELS.get(cat, cat) or '未知'


def _display_log(log):
    """列表展示用副本：仅归一化旧数据英文分类，不污染缓存中的原始记录。"""
    if not isinstance(log, dict):
        return log
    display = dict(log)
    raw_cat = str(log.get('category') or '').strip()
    if not raw_cat or raw_cat in CATEGORY_LABELS:
        display['category'] = _normalize_category(log)
    return display


def _persist_rules(rules: list) -> None:
    """Persist compliance rules to JSON file (DATA_DIR/compliance_rules.json)。

    与启动加载/规则管理同一路径，避免读写分叉导致规则重启后回退。
    """
    from services.fetcher import save_json_file
    try:
        save_json_file(COMPLIANCE_RULES_FILE, list(rules))
    except Exception as e:
        logger.warning(f"Failed to persist rules to file: {e}")

def _sanitize_rule_payload(payload, *, partial=False):
    """Validate and normalize compliance rule mutation payloads."""
    if not isinstance(payload, dict):
        raise ValueError('Request body must be a JSON object')

    allowed_keys = {'rule_name', 'rule_type', 'rule_content', 'severity', 'category', 'enabled', 'applicable_to'}
    unknown_keys = set(payload.keys()) - allowed_keys
    if unknown_keys:
        raise ValueError(f'Unsupported rule fields: {sorted(unknown_keys)}')

    cleaned = {}

    if 'rule_name' in payload:
        rule_name = payload['rule_name']
        if not isinstance(rule_name, str):
            raise ValueError('rule_name must be a string')
        rule_name = rule_name.strip()
        if not rule_name or len(rule_name) > 200:
            raise ValueError('rule_name must be 1-200 characters long')
        cleaned['rule_name'] = rule_name
    elif not partial:
        raise ValueError('rule_name is required')

    if 'rule_type' in payload:
        rule_type = str(payload['rule_type']).upper()
        if rule_type not in ALLOWED_RULE_TYPES:
            raise ValueError(f'rule_type must be one of {sorted(ALLOWED_RULE_TYPES)}')
        cleaned['rule_type'] = rule_type
    elif not partial:
        cleaned['rule_type'] = 'KEYWORD'

    if 'rule_content' in payload:
        rule_content = payload['rule_content']
        if not isinstance(rule_content, dict):
            raise ValueError('rule_content must be an object')
        if len(str(rule_content)) > 20000:
            raise ValueError('rule_content is too large')
        cleaned['rule_content'] = rule_content
    elif not partial:
        cleaned['rule_content'] = {}

    if 'severity' in payload:
        severity = str(payload['severity']).upper()
        if severity not in ALLOWED_SEVERITIES:
            raise ValueError(f'severity must be one of {sorted(ALLOWED_SEVERITIES)}')
        cleaned['severity'] = severity
    elif not partial:
        cleaned['severity'] = 'MEDIUM'

    if 'category' in payload:
        category = payload['category']
        if not isinstance(category, str):
            raise ValueError('category must be a string')
        category = category.strip()
        if not category or len(category) > 100:
            raise ValueError('category must be 1-100 characters long')
        cleaned['category'] = category
    elif not partial:
        cleaned['category'] = '通用'

    if 'enabled' in payload:
        enabled = payload['enabled']
        if not isinstance(enabled, bool):
            raise ValueError('enabled must be a boolean')
        cleaned['enabled'] = enabled
    elif not partial:
        cleaned['enabled'] = True

    # applicable_to: 支持 ['product', 'work']，默认 ['product'] 兼容旧规则
    if 'applicable_to' in payload:
        applicable_to = payload['applicable_to']
        if not isinstance(applicable_to, list):
            raise ValueError('applicable_to must be an array')
        valid_targets = {'product', 'work'}
        for t in applicable_to:
            if t not in valid_targets:
                raise ValueError(f'applicable_to must contain only "product" or "work", got: {t}')
        if not applicable_to:
            raise ValueError('applicable_to cannot be empty')
        cleaned['applicable_to'] = applicable_to
    elif not partial:
        cleaned['applicable_to'] = ['product']  # 默认仅适用于商品，兼容旧规则

    return cleaned


@compliance_bp.route('/compliance', methods=['GET'])
def get_compliance():
    """Get compliance check list with filtering."""
    page = _parse_page(request.args.get('page', 1), 1, minimum=1, maximum=10000)
    size = _parse_page(request.args.get('size', 20), 20, minimum=1, maximum=100)
    status_filter = request.args.get('status', '').strip() or None
    target_type = request.args.get('target_type', '').strip() or None
    rule_id = request.args.get('rule_id', '').strip() or None

    logs = _ensure_list(cache.get(CACHE_KEYS['compliance_logs'], DEFAULT_COMPLIANCE))

    if status_filter:
        logs = [l for l in logs if l.get('status') == status_filter]
    if target_type:
        logs = [l for l in logs if l.get('target_type') == target_type]
    if rule_id:
        logs = [l for l in logs if l.get('rule_id') == rule_id]

    total = len(logs)
    start = (page - 1) * size
    end = start + size

    return success_response({
        'items': [_display_log(l) for l in logs[start:end]],
        'total': total,
        'page': page,
        'size': size
    })


@compliance_bp.route('/compliance/<item_id>/ignore', methods=['POST'])
def ignore_compliance(item_id: str):
    """Ignore a compliance issue."""
    logs = _ensure_list(cache.get(CACHE_KEYS['compliance_logs'], DEFAULT_COMPLIANCE))
    log = next((l for l in logs if l.get('id') == item_id), None)
    if not log:
        return not_found_response('Compliance log')

    log['status'] = 'ignored'
    log['ignored_at'] = datetime.now().isoformat()
    log['ignored_by'] = 'user'
    cache.set(CACHE_KEYS['compliance_logs'], logs)
    _persist_compliance_logs(logs)

    return success_response(log, 'Compliance issue ignored')


@compliance_bp.route('/compliance/<item_id>/take-down', methods=['POST'])
def take_down_compliance(item_id: str):
    """Take down content for compliance issue."""
    logs = _ensure_list(cache.get(CACHE_KEYS['compliance_logs'], DEFAULT_COMPLIANCE))
    log = next((l for l in logs if l.get('id') == item_id), None)
    if not log:
        return not_found_response('Compliance log')

    log['status'] = 'taken_down'
    log['taken_down_at'] = datetime.now().isoformat()
    log['taken_down_by'] = 'user'
    cache.set(CACHE_KEYS['compliance_logs'], logs)
    _persist_compliance_logs(logs)

    return success_response(log, 'Content taken down')


@compliance_bp.route('/compliance/<item_id>/restore', methods=['POST'])
def restore_compliance(item_id: str):
    """Restore taken-down content for compliance issue."""
    logs = _ensure_list(cache.get(CACHE_KEYS['compliance_logs'], DEFAULT_COMPLIANCE))
    log = next((l for l in logs if l.get('id') == item_id), None)
    if not log:
        return not_found_response('Compliance log')

    log['status'] = 'restored'
    log['restored_at'] = datetime.now().isoformat()
    log['restored_by'] = 'user'
    cache.set(CACHE_KEYS['compliance_logs'], logs)
    _persist_compliance_logs(logs)

    return success_response(log, 'Content restored')


@compliance_bp.route('/compliance/stats', methods=['GET'])
def get_compliance_stats():
    """Get compliance statistics."""
    logs = _ensure_list(cache.get(CACHE_KEYS['compliance_logs'], DEFAULT_COMPLIANCE))
    rules = _ensure_list(cache.get(CACHE_KEYS['compliance_rules'], []))

    stats = {
        'total_checks': len(logs),
        'passed': len([l for l in logs if l.get('status') == 'pass']),
        'failed': len([l for l in logs if l.get('status') == 'fail']),
        'warning': len([l for l in logs if l.get('status') == 'warning']),
        'ignored': len([l for l in logs if l.get('status') == 'ignored']),
        'taken_down': len([l for l in logs if l.get('status') == 'taken_down']),
        'error': len([l for l in logs if l.get('status') == 'error']),
        'by_category': {},
        'by_rule': {},
    }

    for log in logs:
        # 分类维度归一化为中文（商品合规/作品合规）：新记录取自身 category，旧记录英文枚举映射
        cat = _normalize_category(log)
        stats['by_category'][cat] = stats['by_category'].get(cat, 0) + 1
        rule = log.get('rule_id', 'unknown')
        stats['by_rule'][rule] = stats['by_rule'].get(rule, 0) + 1

    return success_response(stats)


@compliance_bp.route('/compliance/check', methods=['POST'])
def run_compliance_check():
    """Run compliance check manually."""
    from services.fetcher import fetch_and_check_compliance
    result = fetch_and_check_compliance()
    return success_response(result)


@compliance_bp.route('/compliance/export', methods=['GET'])
def export_compliance():
    """Export compliance data."""
    logs = _ensure_list(cache.get(CACHE_KEYS['compliance_logs'], DEFAULT_COMPLIANCE))
    rules = _ensure_list(cache.get(CACHE_KEYS['compliance_rules'], []))

    return success_response({
        'logs': logs,
        'rules': rules,
        'exported_at': datetime.now().isoformat()
    })


@compliance_bp.route('/compliance/check/products', methods=['POST'])
def check_products():
    """Run compliance check on real Douyin shop products.
    
    Fetches products from Redis cache (products), enriches each product
    with Haohuo preview data (images, specs, price config, jump_url), and runs
    all enabled product rules against the combined data.
    Results are logged to compliance_items with target_type='product'.
    """
    from services.fetcher import load_json_file, CACHE_KEYS as FK, PRODUCTS_FILE

    # 获取产品数据：优先从 Redis cache（与同步任务写入的 key 保持一致）
    products_data = cache.get(FK['products'], None)
    if products_data is None:
        # 回退到同步任务持久化的真实快照（DATA_DIR/products.json），非模拟数据
        if PRODUCTS_FILE.exists():
            products_data = load_json_file(PRODUCTS_FILE, [], model_type='products')
            cache.set(FK['products'], products_data)
        else:
            return success_response({
                'status': 'no_data',
                'message': 'No product data found. Run sync products first.',
                'checked': 0,
                'violations': 0,
                'haohuo_enriched': 0,
                'haohuo_failed': 0
            })
    
    # 获取已启用的规则：过滤适用商品目标的规则（applicable_to 缺失的旧规则默认适用全部目标，
    # 与周期任务 fetch_and_check_compliance 同一口径）
    rules = _ensure_list(cache.get(CACHE_KEYS['compliance_rules'], []))
    enabled_rules = filter_rules_for_target(rules, 'product')

    if not enabled_rules:
        return success_response({
            'status': 'no_rules',
            'message': 'No enabled compliance rules found. Create rules first.',
            'checked': 0,
            'violations': 0,
            'haohuo_enriched': 0,
            'haohuo_failed': 0
        })

    # 使用现有 rule_engine 进行检查
    engine = get_rule_engine()
    checked = 0
    violation_entries = []
    haohuo_enriched = 0
    haohuo_failed = 0
    # 规则 severity 映射：插件 outcome 多数不带 severity，由规则配置兜底传导到违规日志
    rule_severity_map = {
        (r.get('rule_id') or r.get('id')): (r.get('severity') or '')
        for r in enabled_rules if isinstance(r, dict)
    }

    for product in products_data:
        product_id = str(product.get('product_id') or product.get('id', ''))
        product_title = product.get('product_name') or product.get('title', '')

        if not product_id:
            continue

        # 基础 target_data（与周期任务同一构建口径）
        target_data = {
            'product_id': product_id,
            'product_title': product_title,
            'description': product.get('description') or product.get('product_intro', ''),
            'category_name': product.get('category_name', ''),
            'price': product.get('price', 0),
            # 保留原始商品完整数据，供规则引用
            '_raw_product': product,
        }

        # 自动拉取 Haohuo 预览数据并合并（公共增强器，失败不阻断检测）
        enriched, haohuo_err = _enrich_product_with_haohuo(target_data, product_id)
        if enriched:
            haohuo_enriched += 1
        if haohuo_err:
            haohuo_failed += 1

        # 对每个规则进行检查
        outcomes = engine.check_all(enabled_rules, target_data, 'product', product_id)

        for outcome in outcomes:
            checked += 1
            status_val = outcome.status.value if hasattr(outcome.status, 'value') else str(outcome.status)
            # 仅记录违规/告警（fail/warning/error），与周期任务口径一致
            if status_val not in COMPLIANCE_LOG_STATUSES:
                continue
            violation_entries.append(build_compliance_log_entry(
                target_type='product',
                target_id=product_id,
                target_name=product_title,
                outcome=outcome,
                category='商品合规',
                severity=rule_severity_map.get(outcome.rule_id, ''),
            ))

    # 统一走 Redis + DATA_DIR/compliance.json 双写（与周期任务同一存储链路，
    # 删除原 compliance_items.json 双轨死文件）
    _append_compliance_logs(violation_entries)

    # 统计结果
    by_category = {}
    by_rule = {}
    for v in violation_entries:
        cat = v.get('category', '商品合规')
        by_category[cat] = by_category.get(cat, 0) + 1
        rule = v.get('rule_id', 'unknown')
        by_rule[rule] = by_rule.get(rule, 0) + 1

    return success_response({
        'status': 'completed',
        'checked': checked,
        'violations': len(violation_entries),
        'haohuo_enriched': haohuo_enriched,
        'haohuo_failed': haohuo_failed,
        'by_category': by_category,
        'by_rule': by_rule,
        'items': violation_entries,
        'message': f'Checked {checked} rules ({haohuo_enriched} enriched with Haohuo, {haohuo_failed} Haohuo failed), found {len(violation_entries)} violations'
    })

@compliance_bp.route('/compliance/check/works', methods=['POST'])
def check_works():
    """Run compliance check on creator works (videos).
    
    Fetches works from Redis cache (creator_works) and runs
    enabled rules with applicable_to containing 'work' against work data.
    Results are logged to compliance_items with target_type='work'.
    """
    from services.fetcher import load_json_file, CACHE_KEYS as FK, CREATOR_WORKS_FILE
    
    # 获取作品数据：优先从 Redis cache
    works_data = cache.get(FK['creator_works'], None)
    if works_data is None:
        # 回退到同步任务持久化的真实快照（DATA_DIR/creator_works.json），非模拟数据
        if CREATOR_WORKS_FILE.exists():
            works_data = load_json_file(CREATOR_WORKS_FILE, [], model_type='creator_works')
            cache.set(FK['creator_works'], works_data)
        else:
            return success_response({
                'status': 'no_data',
                'message': 'No works data found. Run sync creator works first.',
                'checked': 0,
                'violations': 0
            })
    
    # 获取已启用的规则：与商品检测同一口径过滤（applicable_to 缺失的旧规则默认适用全部目标）
    rules = _ensure_list(cache.get(CACHE_KEYS['compliance_rules'], []))
    enabled_rules = filter_rules_for_target(rules, 'work')

    if not enabled_rules:
        return success_response({
            'status': 'no_rules',
            'message': 'No enabled compliance rules for works found. Create rules first.',
            'checked': 0,
            'violations': 0
        })

    # 使用现有 rule_engine 进行检查
    engine = get_rule_engine()
    checked = 0
    violation_entries = []
    # 规则 severity 映射：插件 outcome 多数不带 severity，由规则配置兜底传导到违规日志
    rule_severity_map = {
        (r.get('rule_id') or r.get('id')): (r.get('severity') or '')
        for r in enabled_rules if isinstance(r, dict)
    }

    for work in works_data:
        work_id = str(work.get('aweme_id') or work.get('id') or work.get('work_id', ''))
        work_title = work.get('title') or work.get('desc') or work.get('work_title', '')

        if not work_id:
            continue

        # 构建 target_data - 作品字段映射
        target_data = {
            'work_id': work_id,
            'work_title': work_title,
            'description': work.get('desc', ''),
            'tags': work.get('tags', []),
            'cover_url': work.get('cover_url', ''),
            'video_url': work.get('video_url', ''),
            'duration': work.get('duration', 0),
            'create_time': work.get('create_time', 0),
            'music_id': work.get('music_id', ''),
            'music_title': work.get('music_title', ''),
            'statistics': work.get('statistics', {}),
            '_raw_work': work,
        }

        # 对每个规则进行检查
        outcomes = engine.check_all(enabled_rules, target_data, 'work', work_id)

        for outcome in outcomes:
            checked += 1
            status_val = outcome.status.value if hasattr(outcome.status, 'value') else str(outcome.status)
            # 仅记录违规/告警（fail/warning/error），统一口径
            if status_val not in COMPLIANCE_LOG_STATUSES:
                continue
            violation_entries.append(build_compliance_log_entry(
                target_type='work',
                target_id=work_id,
                target_name=work_title[:100],
                outcome=outcome,
                category='作品合规',
                severity=rule_severity_map.get(outcome.rule_id, ''),
            ))

    # 统一走 Redis + DATA_DIR/compliance.json 双写
    _append_compliance_logs(violation_entries)

    # 统计结果
    by_category = {}
    by_rule = {}
    for v in violation_entries:
        cat = v.get('category', '作品合规')
        by_category[cat] = by_category.get(cat, 0) + 1
        rule = v.get('rule_id', 'unknown')
        by_rule[rule] = by_rule.get(rule, 0) + 1

    fail_count = len([v for v in violation_entries if v.get('status') == 'fail'])
    warning_count = len([v for v in violation_entries if v.get('status') == 'warning'])

    return success_response({
        'status': 'completed',
        'checked': checked,
        'violations': fail_count,
        'warnings': warning_count,
        'by_category': by_category,
        'by_rule': by_rule,
        'items': violation_entries,
        'message': f'Checked {checked} rules, found {fail_count} violations, {warning_count} warnings'
    })

# Compliance Rules endpoints
@compliance_bp.route('/compliance/rules', methods=['GET'])
def get_compliance_rules():
    """Get compliance rules list."""
    rules = _ensure_list(cache.get(CACHE_KEYS['compliance_rules'], []))
    return success_response({'items': rules, 'total': len(rules)})


@compliance_bp.route('/compliance/rules', methods=['POST'])
def create_compliance_rule():
    """Create new compliance rule."""
    payload = request.get_json(silent=True)
    if payload is None:
        return bad_request_response('Invalid data')

    try:
        sanitized = _sanitize_rule_payload(payload)
    except ValueError as exc:
        return bad_request_response(str(exc))

    rule = {
        'id': f"rule_{int(datetime.now().timestamp())}",
        'rule_name': sanitized['rule_name'],
        'rule_type': sanitized['rule_type'],
        'rule_content': sanitized['rule_content'],
        'severity': sanitized['severity'],
        'category': sanitized['category'],
        'enabled': sanitized['enabled'],
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }

    rules = _ensure_list(cache.get(CACHE_KEYS['compliance_rules'], []))
    rules.insert(0, rule)
    cache.set(CACHE_KEYS['compliance_rules'], rules)
    
    # 同步持久化到 JSON 文件（跨容器重启生效，DATA_DIR 统一路径）
    _persist_rules(rules)

    return success_response(rule, 'Compliance rule created', 201)


@compliance_bp.route('/compliance/rules/<rule_id>', methods=['PUT'])
def update_compliance_rule(rule_id: str):
    """Update compliance rule."""
    rules = _ensure_list(cache.get(CACHE_KEYS['compliance_rules'], []))
    rule = next((r for r in rules if r.get('id') == rule_id), None)
    if not rule:
        return not_found_response('Rule')

    payload = request.get_json(silent=True)
    if payload is None:
        return bad_request_response('Invalid data')

    try:
        sanitized = _sanitize_rule_payload(payload, partial=True)
    except ValueError as exc:
        return bad_request_response(str(exc))

    for key, value in sanitized.items():
        rule[key] = value
    rule['updated_at'] = datetime.now().isoformat()

    cache.set(CACHE_KEYS['compliance_rules'], rules)
    _persist_rules(rules)
    return success_response(rule, 'Compliance rule updated')


@compliance_bp.route('/compliance/rules/<rule_id>', methods=['DELETE'])
def delete_compliance_rule(rule_id: str):
    """Delete compliance rule."""
    rules = _ensure_list(cache.get(CACHE_KEYS['compliance_rules'], []))
    rule = next((r for r in rules if r.get('id') == rule_id), None)
    if not rule:
        return not_found_response('Rule')

    rules = [r for r in rules if r.get('id') != rule_id]
    cache.set(CACHE_KEYS['compliance_rules'], rules)
    _persist_rules(rules)
    return success_response(None, 'Compliance rule deleted')


@compliance_bp.route('/compliance/refresh', methods=['POST'])
def refresh_compliance_cache():
    """Refresh compliance cache from JSON files.
    
    Force reload compliance rules and logs from JSON files into Redis cache.
    Useful when JSON files have been updated but cache still contains stale data.
    """
    from services.fetcher import cache, CACHE_KEYS, load_json_file
    # 重新加载规则到缓存（load_json_file 要求 Path 对象，不能传 str）
    # 同时补齐缺失的好货规则，保证刷新后检测链路完整
    rules_file = COMPLIANCE_RULES_FILE
    if rules_file.exists():
        rules = load_json_file(rules_file, [], model_type='compliance_rules')
        merged_rules, added_ids = ensure_haohuo_rules(rules)
        if added_ids:
            logger.warning(f"Haohuo rules missing on refresh, auto-added: {added_ids}")
            _persist_rules(merged_rules)
        cache.set(CACHE_KEYS['compliance_rules'], merged_rules)
        logger.info(f"Refreshed {len(merged_rules)} compliance rules from file")
    else:
        logger.warning("compliance_rules.json not found, keeping existing cache")

    # 重新加载日志到缓存
    logs_file = COMPLIANCE_FILE
    if logs_file.exists():
        logs = load_json_file(logs_file, [])
        cache.set(CACHE_KEYS['compliance_logs'], logs)
        logger.info(f"Refreshed {len(logs)} compliance logs from file")
    else:
        logger.warning("compliance.json not found, keeping existing cache")

    return success_response({'refreshed': True, 'message': 'Compliance cache refreshed from files'})


@compliance_bp.route('/compliance/rules/<rule_id>/history', methods=['GET'])
def get_compliance_rule_history(rule_id: str):
    """Get compliance rule check history."""
    logs = _ensure_list(cache.get(CACHE_KEYS['compliance_logs'], []))
    rule_logs = [l for l in logs if l.get('rule_id') == rule_id]
    return success_response({'items': rule_logs, 'total': len(rule_logs)})


@compliance_bp.route('/external/creator/income/summary', methods=['GET'])
def get_creator_income_summary():
    """Get creator income summary from external Creator Platform API."""
    from services.fetcher import fetch_external_creator_income
    result = fetch_external_creator_income()
    return success_response(result)


@compliance_bp.route('/external/creator/income/detail', methods=['GET'])
def get_creator_income_detail():
    """Get creator income detail/trend from external Creator Platform API."""
    from services.fetcher import fetch_external_creator_income_detail
    result = fetch_external_creator_income_detail()
    return success_response(result)


@compliance_bp.route('/external/compass/shop/core-index', methods=['GET'])
def get_compass_shop_core_index():
    """Get shop core index data from Compass API."""
    from services.fetcher import fetch_compass_shop_core_index
    result = fetch_compass_shop_core_index()
    return success_response(result)


@compliance_bp.route('/external/haohuo/product/preview', methods=['POST'])
def get_haohuo_product_preview():
    """Get product online preview from Haohuo (好货) platform.
    
    调用好货平台商品在线预览 API：
    POST https://haohuo.jinritemai.com/aweme/v2/shop/promotion/pack/detail/
    
    Request body:
    - promotion_id: 商品推广ID (product_id)，必填
    
    Returns product preview data including:
    - detail_imgs: 详情图片列表
    - product_format: 商品规格信息
    - detail_config: 详情配置（价格说明、销量说明、协议等）
    - detail_imgs_new: 新格式详情图片（含 pic_type）
    - title_image: 标题图片
    - jump_url: 跳转链接（直播间/lynxview）
    - extra: 额外信息
    """
    from services.fetcher import fetch_haohuo_product_preview
    from flask import request
    
    data = request.get_json(silent=True) or {}
    promotion_id = data.get('promotion_id', '').strip()
    
    if not promotion_id:
        from utils.responses import bad_request_response
        return bad_request_response('promotion_id is required')
    
    result = fetch_haohuo_product_preview(promotion_id)
    return success_response(result)
