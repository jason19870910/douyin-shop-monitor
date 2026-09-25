"""Compliance blueprint."""
from flask import Blueprint, request
from services.fetcher import cache, CACHE_KEYS, DEFAULT_COMPLIANCE
from datetime import datetime
from utils.responses import success_response, not_found_response, bad_request_response

compliance_bp = Blueprint('compliance', __name__, url_prefix='/api/v1')

ALLOWED_RULE_TYPES = {'KEYWORD', 'REGEX', 'PRICE', 'LICENSE', 'ML_MODEL', 'CUSTOM_SCRIPT'}
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


def _sanitize_rule_payload(payload, *, partial=False):
    """Validate and normalize compliance rule mutation payloads."""
    if not isinstance(payload, dict):
        raise ValueError('Request body must be a JSON object')

    allowed_keys = {'rule_name', 'rule_type', 'rule_content', 'severity', 'category', 'enabled'}
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
        'items': logs[start:end],
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

    return success_response(log, 'Content taken down')


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
        'by_category': {},
        'by_rule': {},
    }

    for log in logs:
        cat = log.get('target_type', 'unknown')
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
    return success_response(None, 'Compliance rule deleted')


@compliance_bp.route('/compliance/rules/<rule_id>/history', methods=['GET'])
def get_compliance_rule_history(rule_id: str):
    """Get compliance rule check history."""
    logs = _ensure_list(cache.get(CACHE_KEYS['compliance_logs'], []))
    rule_logs = [l for l in logs if l.get('rule_id') == rule_id]
    return success_response({'items': rule_logs, 'total': len(rule_logs)})