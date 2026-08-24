"""
Migration V002: Add Compliance Rule Engine Support
Add support for ML_MODEL and CUSTOM_SCRIPT rule types.

Run: python -m migrations migrate
"""
import logging

logger = logging.getLogger(__name__)


def upgrade():
    """Apply migration - add compliance rule engine fields."""
    logger.info("Applying migration V002: Compliance Rule Engine Support")
    
    from services.fetcher import cache, CACHE_KEYS
    
    # Get existing compliance rules
    existing_rules = cache.get(CACHE_KEYS.get('compliance_rules', 'compliance_rules'), [])
    
    # Add new rule examples for ML_MODEL and CUSTOM_SCRIPT
    new_rules = [
        {
            'id': 'rule_004',
            'rule_name': '图片违规内容检测 (NSFW)',
            'rule_type': 'ML_MODEL',
            'rule_content': {
                'model_endpoint': 'http://ml-service:8000/api/v1/classify',
                'model_type': 'image_classification',
                'input_field': 'cover_url',
                'threshold': 0.8,
                'labels': ['nsfw', 'violence', 'gore', 'political'],
                'timeout_seconds': 30
            },
            'severity': 'HIGH',
            'category': '图片审核',
            'enabled': False,  # Disabled by default, requires ML service
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        },
        {
            'id': 'rule_005',
            'rule_name': '视频内容安全分析',
            'rule_type': 'ML_MODEL',
            'rule_content': {
                'model_endpoint': 'http://ml-service:8000/api/v1/video_analyze',
                'model_type': 'video_analysis',
                'input_field': 'video_url',
                'threshold': 0.75,
                'labels': ['violence', 'pornography', 'illegal', 'sensitive'],
                'timeout_seconds': 120
            },
            'severity': 'HIGH',
            'category': '视频审核',
            'enabled': False,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        },
        {
            'id': 'rule_006',
            'rule_name': '自定义合规脚本 - 价格异常检测',
            'rule_type': 'CUSTOM_SCRIPT',
            'rule_content': {
                'script': '''
# 自定义脚本：检测价格异常
# 可用变量: context, target, config, result

price = target.get('price', 0)
category = target.get('category', '')

# 类别价格阈值
category_thresholds = {
    '服饰': (10, 500),
    '电子': (50, 10000),
    '家居': (20, 2000),
    '美妆': (15, 800),
}

if category in category_thresholds:
    min_price, max_price = category_thresholds[category]
    if price < min_price or price > max_price:
        result['status'] = 'fail'
        result['message'] = f'价格异常: {category} 类商品价格 {price} 超出正常范围 ({min_price}-{max_price})'
        result['details'] = {'price': price, 'category': category, 'min': min_price, 'max': max_price}
        result['matched_content'] = f'价格 {price} 元'
    else:
        result['status'] = 'pass'
        result['message'] = '价格在正常范围内'
else:
    result['status'] = 'pass'
    result['message'] = '未识别类别，跳过价格检查'
''',
                'language': 'python',
                'timeout_seconds': 10,
                'allowed_imports': ['json', 're', 'datetime']
            },
            'severity': 'MEDIUM',
            'category': '价格监管',
            'enabled': True,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
    ]
    
    # Append new rules
    for rule in new_rules:
        # Check if rule already exists
        if not any(r.get('id') == rule['id'] for r in existing_rules):
            existing_rules.append(rule)
            logger.info(f"Added new compliance rule: {rule['rule_name']} ({rule['rule_type']})")
    
    cache.set(CACHE_KEYS.get('compliance_rules', 'compliance_rules'), existing_rules)
    logger.info("Migration V002 completed - ML_MODEL and CUSTOM_SCRIPT rules added")


def downgrade():
    """Rollback migration - remove added rules."""
    logger.info("Rolling back migration V002: Compliance Rule Engine Support")
    
    from services.fetcher import cache, CACHE_KEYS
    
    existing_rules = cache.get(CACHE_KEYS.get('compliance_rules', 'compliance_rules'), [])
    
    # Remove rules added in this migration
    rule_ids_to_remove = {'rule_004', 'rule_005', 'rule_006'}
    original_count = len(existing_rules)
    existing_rules = [r for r in existing_rules if r.get('id') not in rule_ids_to_remove]
    removed_count = original_count - len(existing_rules)
    
    cache.set(CACHE_KEYS.get('compliance_rules', 'compliance_rules'), existing_rules)
    logger.info(f"Removed {removed_count} compliance rules")
    logger.info("Migration V002 rolled back")