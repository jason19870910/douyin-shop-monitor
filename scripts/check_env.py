#!/usr/bin/env python3
"""
环境变量一致性检查脚本
对比 .env.example 与 config.py 中实际使用的环境变量
"""

import os
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
ENV_EXAMPLE = PROJECT_ROOT / '.env.example'
CONFIG_FILE = PROJECT_ROOT / 'config.py'
APP_FILE = PROJECT_ROOT / 'app.py'


def parse_env_example(filepath: Path) -> dict:
    """解析 .env.example 文件，返回变量名 -> (默认值, 注释)"""
    variables = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            # 处理 VAR=value 格式
            match = re.match(r'^([A-Z_][A-Z0-9_]*)=(.*)$', line)
            if match:
                var_name = match.group(1)
                default_val = match.group(2)
                variables[var_name] = {
                    'default': default_val,
                    'line': line_num,
                    'defined_in_example': True
                }
    return variables


def parse_config_py(filepath: Path) -> dict:
    """解析 config.py 中 os.getenv 调用"""
    variables = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 匹配 os.getenv('VAR_NAME', 'default') 或 os.getenv("VAR_NAME", "default")
    # 也支持多行和各种格式
    pattern = r'os\.getenv\s*\(\s*[\'"]([A-Z_][A-Z0-9_]*)[\'"]'
    matches = re.finditer(pattern, content)

    for match in matches:
        var_name = match.group(1)
        if var_name not in variables:
            variables[var_name] = {}
        variables[var_name]['used_in_config'] = True

    return variables


def parse_app_py(filepath: Path) -> dict:
    """解析 app.py 中直接使用 os.getenv 或 Config.ATTR 的情况"""
    variables = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 匹配 os.getenv('VAR_NAME')
    pattern1 = r'os\.getenv\s*\(\s*[\'"]([A-Z_][A-Z0-9_]*)[\'"]'
    for match in re.finditer(pattern1, content):
        var_name = match.group(1)
        if var_name not in variables:
            variables[var_name] = {}
        variables[var_name]['used_in_app'] = True

    # 匹配 Config.VAR_NAME 访问
    pattern2 = r'Config\.([A-Z_][A-Z0-9_]*)'
    # 非环境变量的配置属性（计算属性、常量、URL拼接等）
    NON_ENV_ATTRS = {
        'SCHEDULE_INTERVAL_MINUTES', 'ALERT_EMAIL', 'DATA_DIR',
        'EXTERNAL_DATA_BASE_URL', 'API_AUTH_TOKEN', 'FXG_BASE_URL',
        'CREATOR_BASE_URL', 'COMMON_HEADERS', 'FXG_COOKIES',
        'CREATOR_COOKIES', '__TOKEN', 'MS_TOKEN', 'a_bogus',
        'verifyFp', 'fp', 'KEEP_ALIVE_TIMEOUT', 'TIMEOUT',
        'API_KEY', 'DOUYIN_APP_ID', 'DOUYIN_APP_SECRET',
        'DOUYIN_ACCESS_TOKEN', 'USER_AGENT', 'CELERY_BROKER_URL',
        'CELERY_RESULT_BACKEND', 'PRODUCT_LIST_URL', 'PRODUCT_STATS_URL',
        'ORDER_SEARCH_URL', 'ORDER_STATS_URL', 'CREATOR_DASHBOARD_URL',
    }
    for match in re.finditer(pattern2, content):
        var_name = match.group(1)
        if var_name in NON_ENV_ATTRS:
            continue
        if var_name not in variables:
            variables[var_name] = {}
        variables[var_name]['used_in_config_attr'] = True

    return variables


def check_consistency():
    """执行一致性检查"""
    print("=" * 80)
    print("环境变量一致性检查报告")
    print("=" * 80)

    # 解析三个源
    env_vars = parse_env_example(ENV_EXAMPLE)
    config_vars = parse_config_py(CONFIG_FILE)
    app_vars = parse_app_py(APP_FILE)

    # 合并所有变量
    all_vars = set(env_vars.keys()) | set(config_vars.keys()) | set(app_vars.keys())

    print(f"\n📋 统计摘要:")
    print(f"  .env.example 中定义: {len(env_vars)} 个")
    print(f"  config.py 中使用:    {len(config_vars)} 个")
    print(f"  app.py 中使用:       {len(app_vars)} 个")
    print(f"  总计唯一变量:         {len(all_vars)} 个")

    # 检查缺失项
    missing_in_example = []
    missing_in_config = []
    missing_in_app = []

    for var in all_vars:
        in_example = var in env_vars
        in_config = var in config_vars
        in_app = var in app_vars

        if not in_example:
            missing_in_example.append(var)
        if not in_config and not in_app:
            missing_in_config.append(var)
        if not in_app and not in_config:
            missing_in_app.append(var)

    # 输出详细结果
    print(f"\n{'='*80}")
    print("✅ 在 .env.example 中定义但代码未使用的变量 (可能过期):")
    unused_in_code = [v for v in env_vars if v not in config_vars and v not in app_vars]
    if unused_in_code:
        for v in sorted(unused_in_code):
            print(f"  - {v} (默认值: {env_vars[v]['default']})")
    else:
        print("  无")

    print(f"\n{'='*80}")
    print("❌ 代码中使用但 .env.example 中缺失的变量 (需补充):")
    if missing_in_example:
        for v in sorted(missing_in_example):
            sources = []
            if v in config_vars:
                sources.append("config.py")
            if v in app_vars:
                sources.append("app.py")
            print(f"  - {v} (使用于: {', '.join(sources)})")
    else:
        print("  无缺失，完美匹配！")

    print(f"\n{'='*80}")
    print("📝 变量详细对照表:")
    print(f"{'变量名':<40} {'示例':<8} {'config.py':<10} {'app.py':<8}")
    print("-" * 70)
    for var in sorted(all_vars):
        ex = "✓" if var in env_vars else "✗"
        cf = "✓" if var in config_vars else "✗"
        ap = "✓" if var in app_vars else "✗"
        print(f"{var:<40} {ex:<8} {cf:<10} {ap:<8}")

    # 返回检查结果
    has_errors = len(missing_in_example) > 0
    return has_errors


def main():
    print(f"项目根目录: {PROJECT_ROOT}")
    print(f".env.example: {ENV_EXAMPLE.exists()}")
    print(f"config.py: {CONFIG_FILE.exists()}")
    print(f"app.py: {APP_FILE.exists()}")

    if not ENV_EXAMPLE.exists():
        print("❌ .env.example 不存在！")
        sys.exit(1)

    has_errors = check_consistency()

    if has_errors:
        print(f"\n⚠️  检查发现不一致，请修复上述缺失变量")
        sys.exit(1)
    else:
        print(f"\n✅ 所有环境变量一致性检查通过！")
        sys.exit(0)


if __name__ == '__main__':
    main()