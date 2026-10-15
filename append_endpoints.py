#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

filepath = r"c:\Users\Administrator\Documents\trae_projects\douyin\src\backend\blueprints\compliance.py"

new_endpoints =r'''

@compliance_bp.route('/version', methods=['GET'])
def get_version():
    """Get current application version and build info."""
    from pathlib import Path
    import json
    import os

    pkg_file = Path(__file__).parent.parent / '..' / '..' / '..' / 'src' / 'frontend' / 'package.json'
    version = 'dev'
    commit = 'unknown'
    built_at = ''

    if pkg_file.exists():
        try:
            with open(pkg_file, 'r', encoding='utf-8') as f:
                pkg = json.load(f)
                version = pkg.get('version', 'dev')
        except Exception:
            pass

    try:
        import subprocess
        result = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            capture_output=True, text=True, cwd=Path(__file__).parent.parent.parent
        )
        if result.returncode == 0:
            commit = result.stdout.strip()
    except Exception:
        pass

    built_at_file = Path(__file__).parent.parent / '..' / '..' / '..' / 'src' / 'frontend' / 'build' / '.built_at'
    if built_at_file.exists():
        try:
            with open(built_at_file, 'r', encoding='utf-8') as f:
                built_at = f.read().strip()
        except Exception:
            pass

    from config import settings
    api_key_configured = bool(settings.API_KEY and settings.API_KEY != 'your_api_key_here')

    return success_response({
        'version': version,
        'commit': commit,
        'builtAt': built_at,
        'apiKeyInlined': api_key_configured,
        'environment': 'production' if not settings.DEBUG else 'development',
    })


@compliance_bp.route('/changes', methods=['GET'])
def get_recent_changes():
    import subprocess
    import json
    from pathlib import Path

    try:
        result = subprocess.run(
            ['git', 'log', '--oneline', '-10'],
            capture_output=True, text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        if result.returncode != 0:
            return success_response([], 'No git history available')

        commits = []
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split(' ', 1)
                commits.append({
                    'id': parts[0] if len(parts) > 0 else '',
                    'message': parts[1] if len(parts) > 1 else line,
                    'author': 'unknown',
                    'date': new Date().toISOString(),
                    'type': 'chore',
                })

        return success_response(commits[:10])
    except Exception as e:
        import logging
        logging.warning(f"Failed to get git changes: {e}")
        return success_response([], 'Failed to read git history')


@compliance_bp.route('/status', methods=['GET'])
def get_status():
    from services.fetcher import cache, CACHE_KEYS
    from pathlib import Path

    redis_healthy = False
    try:
        redis_result = subprocess.run(
            ['redis-cli', 'ping'],
            capture_output=True, text=True
        )
        redis_healthy = redis_result.returncode == 0
    except Exception:
        pass

    app_healthy = False
    try:
        logs = _ensure_list(cache.get(CACHE_KEYS['compliance_logs'], []))
        app_healthy = len(logs) >= 0
    except Exception:
        pass

    frontend_healthy = True
    last_deploy = ''

    return success_response({
        'appHealthy': app_healthy,
        'redisHealthy': redis_healthy,
        'frontendHealthy': frontend_healthy,
        'lastDeploy': last_deploy,
    })


@compliance_bp.route('/env', methods=['GET'])
def get_env_config():
    from config import settings
    import os

    return success_response({
        'VITE_API_KEY': settings.API_KEY or os.getenv('VITE_API_KEY', '') or 'your_api_key_here',
        'VITE_DEV_MODE': getattr(settings, 'DEBUG', True),
        'VITE_ENABLE_MOCK_FALLBACK': getattr(settings, 'VITE_ENABLE_MOCK_FALLBACK', False),
    })
'''

with open(filepath, 'a', encoding='utf-8') as f:
    f.write(new_endpoints)

print("成功追加新 API 端点到", filepath)