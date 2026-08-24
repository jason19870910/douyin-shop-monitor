import re

with open('/opt/app/opt/douyin-platform/apps/monitor/app.py', 'r') as f:
    content = f.read()

# Fix get_compliance to read from file
old_get_compliance = '''@app.route('/api/compliance', methods=['GET'])
def get_compliance():
    """Get compliance list with filtering."""
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 20))
    keyword = request.args.get('keyword', '').lower()
    risk_filter = request.args.get('risk_level')
    status_filter = request.args.get('status')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    compliance = data_cache['compliance']

    if keyword:
        compliance = [c for c in compliance if keyword in c.get('product_name', '').lower() or keyword in c.get('product_id', '').lower()]
    if risk_filter:
        compliance = [c for c in compliance if c.get('risk_level') == risk_filter]
    if status_filter:
        compliance = [c for c in compliance if c.get('status') == status_filter]
    if start_date:
        compliance = [c for c in compliance if c.get('detected_at', '') >= start_date]
    if end_date:
        compliance = [c for c in compliance if c.get('detected_at', '') <= end_date]

    total = len(compliance)
    start = (page - 1) * size
    end = start + size

    return jsonify({
        'data': compliance[start:end],
        'total': total,
        'page': page,
        'size': size
    })'''

new_get_compliance = '''@app.route('/api/compliance', methods=['GET'])
def get_compliance():
    """Get compliance list with filtering."""
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 20))
    keyword = request.args.get('keyword', '').lower()
    risk_filter = request.args.get('risk_level')
    status_filter = request.args.get('status')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    compliance = load_json_file(COMPLIANCE_FILE, [])

    if keyword:
        compliance = [c for c in compliance if keyword in c.get('product_name', '').lower() or keyword in c.get('product_id', '').lower()]
    if risk_filter:
        compliance = [c for c in compliance if c.get('risk_level') == risk_filter]
    if status_filter:
        compliance = [c for c in compliance if c.get('status') == status_filter]
    if start_date:
        compliance = [c for c in compliance if c.get('detected_at', '') >= start_date]
    if end_date:
        compliance = [c for c in compliance if c.get('detected_at', '') <= end_date]

    total = len(compliance)
    start = (page - 1) * size
    end = start + size

    return jsonify({
        'data': compliance[start:end],
        'total': total,
        'page': page,
        'size': size
    })'''

content = content.replace(old_get_compliance, new_get_compliance)

# Fix ignore_compliance
old_ignore = '''@app.route('/api/compliance/<item_id>/ignore', methods=['POST'])
def ignore_compliance(item_id: str):
    """Ignore compliance issue."""
    item = next((c for c in data_cache['compliance'] if c.get('product_id') == item_id), None)
    if not item:
        return jsonify({'error': 'Compliance item not found'}), 404

    item['status'] = 'ignored'
    item['ignored_at'] = datetime.now().isoformat()
    save_all_data()
    return jsonify({'data': item, 'message': 'Compliance issue ignored'})'''

new_ignore = '''@app.route('/api/compliance/<item_id>/ignore', methods=['POST'])
def ignore_compliance(item_id: str):
    """Ignore compliance issue."""
    compliance = load_json_file(COMPLIANCE_FILE, [])
    item = next((c for c in compliance if c.get('product_id') == item_id), None)
    if not item:
        return jsonify({'error': 'Compliance item not found'}), 404

    item['status'] = 'ignored'
    item['ignored_at'] = datetime.now().isoformat()
    save_json_file(COMPLIANCE_FILE, compliance)
    # Also update cache for current worker
    cache_item = next((c for c in data_cache['compliance'] if c.get('product_id') == item_id), None)
    if cache_item:
        cache_item['status'] = 'ignored'
        cache_item['ignored_at'] = item['ignored_at']
    return jsonify({'data': item, 'message': 'Compliance issue ignored'})'''

content = content.replace(old_ignore, new_ignore)

# Fix take_down_compliance
old_take_down = '''@app.route('/api/compliance/<item_id>/take-down', methods=['POST'])
def take_down_compliance(item_id: str):
    """Take down product for compliance violation."""
    item = next((c for c in data_cache['compliance'] if c.get('product_id') == item_id), None)
    if not item:
        return jsonify({'error': 'Compliance item not found'}), 404

    item['status'] = 'resolved'
    item['resolved_at'] = datetime.now().isoformat()
    item['resolution'] = 'taken_down'
    save_all_data()
    return jsonify({'data': item, 'message': 'Product taken down'})'''

new_take_down = '''@app.route('/api/compliance/<item_id>/take-down', methods=['POST'])
def take_down_compliance(item_id: str):
    """Take down product for compliance violation."""
    compliance = load_json_file(COMPLIANCE_FILE, [])
    item = next((c for c in compliance if c.get('product_id') == item_id), None)
    if not item:
        return jsonify({'error': 'Compliance item not found'}), 404

    item['status'] = 'resolved'
    item['resolved_at'] = datetime.now().isoformat()
    item['resolution'] = 'taken_down'
    save_json_file(COMPLIANCE_FILE, compliance)
    # Also update cache for current worker
    cache_item = next((c for c in data_cache['compliance'] if c.get('product_id') == item_id), None)
    if cache_item:
        cache_item['status'] = 'resolved'
        cache_item['resolved_at'] = item['resolved_at']
        cache_item['resolution'] = 'taken_down'
    return jsonify({'data': item, 'message': 'Product taken down'})'''

content = content.replace(old_take_down, new_take_down)

# Fix restore_compliance
old_restore = '''@ app.route('/api/compliance/<item_id>/restore', methods=['POST'])
def restore_compliance(item_id: str):
    """Restore compliance issue from ignored."""
    item = next((c for c in data_cache['compliance'] if c.get('product_id') == item_id), None)
    if not item:
        return jsonify({'error': 'Compliance item not found'}), 404

    item['status'] = 'pending'
    item['restored_at'] = datetime.now().isoformat()
    save_all_data()
    return jsonify({'data': item, 'message': 'Compliance issue restored'})'''

new_restore = '''@app.route('/api/compliance/<item_id>/restore', methods=['POST'])
def restore_compliance(item_id: str):
    """Restore compliance issue from ignored."""
    compliance = load_json_file(COMPLIANCE_FILE, [])
    item = next((c for c in compliance if c.get('product_id') == item_id), None)
    if not item:
        return jsonify({'error': 'Compliance item not found'}), 404

    item['status'] = 'pending'
    item['restored_at'] = datetime.now().isoformat()
    save_json_file(COMPLIANCE_FILE, compliance)
    # Also update cache for current worker
    cache_item = next((c for c in data_cache['compliance'] if c.get('product_id') == item_id), None)
    if cache_item:
        cache_item['status'] = 'pending'
        cache_item['restored_at'] = item['restored_at']
    return jsonify({'data': item, 'message': 'Compliance issue restored'})'''

content = content.replace(old_restore, new_restore)

# Fix export_compliance
old_export = '''@app.route('/api/compliance/export', methods=['GET'])
def export_compliance():
    """Export compliance report as CSV."""
    import csv
    import io

    compliance = data_cache['compliance']

    # Apply same filters as get_compliance
    keyword = request.args.get('keyword', '').lower()
    risk_filter = request.args.get('risk_level')
    status_filter = request.args.get('status')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if keyword:
        compliance = [c for c in compliance if keyword in c.get('product_name', '').lower() or keyword in c.get('product_id', '').lower()]
    if risk_filter:
        compliance = [c for c in compliance if c.get('risk_level') == risk_filter]
    if status_filter:
        compliance = [c for c in compliance if c.get('status') == status_filter]
    if start_date:
        compliance = [c for c in compliance if c.get('detected_at', '') >= start_date]
    if end_date:
        compliance = [c for c in compliance if c.get('detected_at', '') <= end_date]'''

new_export = '''@app.route('/api/compliance/export', methods=['GET'])
def export_compliance():
    """Export compliance report as CSV."""
    import csv
    import io

    compliance = load_json_file(COMPLIANCE_FILE, [])

    # Apply same filters as get_compliance
    keyword = request.args.get('keyword', '').lower()
    risk_filter = request.args.get('risk_level')
    status_filter = request.args.get('status')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if keyword:
        compliance = [c for c in compliance if keyword in c.get('product_name', '').lower() or keyword in c.get('product_id', '').lower()]
    if risk_filter:
        compliance = [c for c in compliance if c.get('risk_level') == risk_filter]
    if status_filter:
        compliance = [c for c in compliance if c.get('status') == status_filter]
    if start_date:
        compliance = [c for c in compliance if c.get('detected_at', '') >= start_date]
    if end_date:
        compliance = [c for c in compliance if c.get('detected_at', '') <= end_date]'''

content = content.replace(old_export, new_export)

with open('/opt/app/opt/douyin-platform/apps/monitor/app.py', 'w') as f:
    f.write(content)

print("Fixed compliance API endpoints!")