import re

with open('/opt/app/opt/douyin-platform/apps/monitor/app.py', 'r') as f:
    content = f.read()

# Use regex to replace fetch_and_check_compliance function
old_pattern = r'def fetch_and_check_compliance\(\) -> dict:.*?check_batch_id = f"check_{int\(datetime\.now\(\)\.timestamp\(\)\)}"'

new_func = '''def fetch_and_check_compliance() -> dict:
    """
    Run compliance check on all products.
    Returns summary of check results.
    """
    logger.info("Running compliance check on all products...")

    # Use fallback to get products and rules (loads mock data if cache empty)
    products, _ = get_data_with_fallback('products', MOCK_PRODUCTS)
    rules, _ = get_data_with_fallback('compliance_rules', DEFAULT_COMPLIANCE_RULES)

    if not products:
        logger.warning("No products to check for compliance")
        return {'checked': 0, 'pass': 0, 'warning': 0, 'fail': 0, 'details': []}

    if not rules:
        logger.warning("No compliance rules configured")
        return {'checked': 0, 'pass': 0, 'warning': 0, 'fail': 0, 'details': []}

    check_batch_id = f"check_{int(datetime.now().timestamp())}"'''

content = re.sub(old_pattern, new_func, content, flags=re.DOTALL)

with open('/opt/app/opt/douyin-platform/apps/monitor/app.py', 'w') as f:
    f.write(content)

print("Fixed fetch_and_check_compliance with regex!")