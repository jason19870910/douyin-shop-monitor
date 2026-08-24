"""Compliance blueprint."""
from flask import Blueprint, request
from services.fetcher import cache, CACHE_KEYS, DEFAULT_COMPLIANCE
from datetime import datetime
from utils.responses import success_response, not_found_response, bad_request_response

compliance_bp = Blueprint('compliance', __name__, url_prefix='/api/v1')


@compliance_bp.route('/compliance', methods=['GET'])
def get_compliance():
    """Get compliance check list with filtering."""
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 20))
    status_filter = request.args.get('status')
    target_type = request.args.get('target_type')
    rule_id = request.args.get('rule_id')
    
    logs = cache.get(CACHE_KEYS['compliance_logs'], DEFAULT_COMPLIANCE)
    
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
    logs = cache.get(CACHE_KEYS['compliance_logs'], DEFAULT_COMPLIANCE)
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
    logs = cache.get(CACHE_KEYS['compliance_logs'], DEFAULT_COMPLIANCE)
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
    logs = cache.get(CACHE_KEYS['compliance_logs'], DEFAULT_COMPLIANCE)
    rules = cache.get(CACHE_KEYS['compliance_rules'], [])
    
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
    logs = cache.get(CACHE_KEYS['compliance_logs'], DEFAULT_COMPLIANCE)
    rules = cache.get(CACHE_KEYS['compliance_rules'], [])
    
    return success_response({
        'logs': logs,
        'rules': rules,
        'exported_at': datetime.now().isoformat()
    })


# Compliance Rules endpoints
@compliance_bp.route('/compliance/rules', methods=['GET'])
def get_compliance_rules():
    """Get compliance rules list."""
    rules = cache.get(CACHE_KEYS['compliance_rules'], [])
    return success_response({'items': rules, 'total': len(rules)})


@compliance_bp.route('/compliance/rules', methods=['POST'])
def create_compliance_rule():
    """Create new compliance rule."""
    data = request.get_json()
    if not data:
        return bad_request_response('Invalid data')
    
    rule = {
        'id': f"rule_{int(datetime.now().timestamp())}",
        'rule_name': data.get('rule_name', ''),
        'rule_type': data.get('rule_type', 'KEYWORD'),
        'rule_content': data.get('rule_content', {}),
        'severity': data.get('severity', 'MEDIUM'),
        'category': data.get('category', '通用'),
        'enabled': data.get('enabled', True),
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    
    rules = cache.get(CACHE_KEYS['compliance_rules'], [])
    rules.insert(0, rule)
    cache.set(CACHE_KEYS['compliance_rules'], rules)
    
    return success_response(rule, 'Compliance rule created', 201)


@compliance_bp.route('/compliance/rules/<rule_id>', methods=['PUT'])
def update_compliance_rule(rule_id: str):
    """Update compliance rule."""
    rules = cache.get(CACHE_KEYS['compliance_rules'], [])
    rule = next((r for r in rules if r.get('id') == rule_id), None)
    if not rule:
        return not_found_response('Rule')
    
    data = request.get_json()
    if not data:
        return bad_request_response('Invalid data')
    
    rule.update({
        'rule_name': data.get('rule_name', rule['rule_name']),
        'rule_type': data.get('rule_type', rule['rule_type']),
        'rule_content': data.get('rule_content', rule['rule_content']),
        'severity': data.get('severity', rule['severity']),
        'category': data.get('category', rule['category']),
        'enabled': data.get('enabled', rule['enabled']),
        'updated_at': datetime.now().isoformat()
    })
    
    cache.set(CACHE_KEYS['compliance_rules'], rules)
    return success_response(rule, 'Compliance rule updated')


@compliance_bp.route('/compliance/rules/<rule_id>', methods=['DELETE'])
def delete_compliance_rule(rule_id: str):
    """Delete compliance rule."""
    rules = cache.get(CACHE_KEYS['compliance_rules'], [])
    rule = next((r for r in rules if r.get('id') == rule_id), None)
    if not rule:
        return not_found_response('Rule')
    
    rules = [r for r in rules if r.get('id') != rule_id]
    cache.set(CACHE_KEYS['compliance_rules'], rules)
    return success_response(None, 'Compliance rule deleted')


@compliance_bp.route('/compliance/rules/<rule_id>/history', methods=['GET'])
def get_compliance_rule_history(rule_id: str):
    """Get compliance rule check history."""
    logs = cache.get(CACHE_KEYS['compliance_logs'], [])
    rule_logs = [l for l in logs if l.get('rule_id') == rule_id]
    return success_response({'items': rule_logs, 'total': len(rule_logs)})