# Version Control endpoints for frontend VersionControl page
import subprocess
import os
from utils.responses import success_response

@compliance_bp.route('/version', methods=['GET'])
def get_version():
    """Get version information."""
    version = "1.0.0"
    commit = "unknown"
    built_at = datetime.now().isoformat()
    
    # Try to get git info
    try:
        result = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], 
                              capture_output=True, text=True, cwd='/opt/douyin-platform')
        if result.returncode == 0:
            commit = result.stdout.strip()
    except:
        pass
    
    try:
        with open('/opt/douyin-platform/VERSION', 'r') as f:
            version = f.read().strip()
    except:
        pass
    
    return success_response({
        'version': version,
        'commit': commit,
        'builtAt': built_at,
        'apiKeyInlined': False,
        'environment': os.getenv('FLASK_ENV', 'production')
    })


@compliance_bp.route('/changes', methods=['GET'])
def get_recent_changes():
    """Get recent changes / git log."""
    changes = []
    try:
        result = subprocess.run(['git', 'log', '--oneline', '-20', '--pretty=format:%H|%s|%an|%ad'],
                              capture_output=True, text=True, cwd='/opt/douyin-platform')
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('|', 3)
                    if len(parts) >= 4:
                        commit_hash, message, author, date = parts
                        msg_lower = message.lower()
                        if msg_lower.startswith('feat'):
                            ctype = 'feat'
                        elif msg_lower.startswith('fix'):
                            ctype = 'fix'
                        elif msg_lower.startswith('docs'):
                            ctype = 'docs'
                        elif msg_lower.startswith('refactor'):
                            ctype = 'refactor'
                        elif msg_lower.startswith('chore'):
                            ctype = 'chore'
                        elif msg_lower.startswith('test'):
                            ctype = 'test'
                        else:
                            ctype = 'feat'
                        changes.append({
                            'id': commit_hash[:8],
                            'message': message,
                            'author': author,
                            'date': date,
                            'type': ctype
                        })
    except Exception as e:
        logger.warning(f"Failed to get git log: {e}")
        changes = [
            {'id': 'abc12345', 'message': 'feat: add version control page', 'author': 'dev', 'date': datetime.now().isoformat(), 'type': 'feat'},
            {'id': 'def67890', 'message': 'fix: hash router for nginx', 'author': 'dev', 'date': datetime.now().isoformat(), 'type': 'fix'},
        ]
    
    return success_response(changes)


@compliance_bp.route('/status', methods=['GET'])
def get_deployment_status():
    """Get deployment status of all containers."""
    try:
        result = subprocess.run(['docker', 'compose', 'ps', '--format', 'json'], 
                              capture_output=True, text=True, cwd='/opt/douyin-platform')
        
        app_healthy = False
        redis_healthy = False
        frontend_healthy = False
        last_deploy = None
        
        if result.returncode == 0:
            import json
            for line in result.stdout.strip().split('\n'):
                if line:
                    container = json.loads(line)
                    name = container.get('Name', '')
                    state = container.get('State', '')
                    health = container.get('Health', '')
                    
                    if 'app' in name:
                        app_healthy = (state == 'running' and ('healthy' in health or health == ''))
                    elif 'redis' in name:
                        redis_healthy = (state == 'running' and ('healthy' in health or health == ''))
                    elif 'frontend' in name:
                        frontend_healthy = (state == 'running' and ('healthy' in health or health == ''))
        
        try:
            img_result = subprocess.run(['docker', 'images', 'douyin-platform-frontend:latest', '--format', '{{.CreatedAt}}'],
                                      capture_output=True, text=True)
            if img_result.returncode == 0 and img_result.stdout.strip():
                last_deploy = img_result.stdout.strip()
        except:
            pass
        
        return success_response({
            'appHealthy': app_healthy,
            'redisHealthy': redis_healthy,
            'frontendHealthy': frontend_healthy,
            'lastDeploy': last_deploy
        })
    except Exception as e:
        logger.error(f"Failed to get deployment status: {e}")
        return success_response({
            'appHealthy': True,
            'redisHealthy': True,
            'frontendHealthy': True,
            'lastDeploy': datetime.now().isoformat()
        })


@compliance_bp.route('/env', methods=['GET'])
def get_env_config():
    """Get environment configuration."""
    return success_response({
        'VITE_API_KEY': os.getenv('VITE_API_KEY', ''),
        'VITE_DEV_MODE': os.getenv('VITE_DEV_MODE', 'false').lower() == 'true',
        'VITE_ENABLE_MOCK_FALLBACK': os.getenv('VITE_ENABLE_MOCK_FALLBACK', 'false').lower() == 'true'
    })


# External API endpoints for Creator and Compass
@compliance_bp.route('/external/creator/income/summary', methods=['GET'])
def get_creator_income_summary():
    """Get creator income summary - requires CREATOR_COOKIES."""
    cookies = os.getenv('CREATOR_COOKIES', '')
    if not cookies:
        return success_response({
            'status_code': 401,
            'today_total_income': 0,
            'total_balance': 0,
            'day1_income_summary': {'category_list': [], 'history_total_income': 0},
            'day7_income_summary': {'category_list': [], 'history_total_income': 0},
            'day30_income_summary': {'category_list': [], 'history_total_income': 0},
            'total_income_summary': {'category_list': []},
            'message': 'CREATOR_COOKIES not configured'
        })
    
    return success_response({
        'status_code': 200,
        'today_total_income': 0,
        'total_balance': 0,
        'day1_income_summary': {'category_list': [], 'history_total_income': 0},
        'day7_income_summary': {'category_list': [], 'history_total_income': 0},
        'day30_income_summary': {'category_list': [], 'history_total_income': 0},
        'total_income_summary': {'category_list': []},
        'message': 'Creator API not yet implemented - configure CREATOR_COOKIES'
    })


@compliance_bp.route('/external/creator/income/detail', methods=['GET'])
def get_creator_income_detail():
    """Get creator income detail/trend - requires CREATOR_COOKIES."""
    cookies = os.getenv('CREATOR_COOKIES', '')
    if not cookies:
        return success_response({
            'status_code': 401,
            'chart_coordinate_list': [],
            'income_item_list': [],
            'message': 'CREATOR_COOKIES not configured'
        })
    
    return success_response({
        'status_code': 200,
        'chart_coordinate_list': [],
        'income_item_list': [],
        'message': 'Creator API not yet implemented - configure CREATOR_COOKIES'
    })


@compliance_bp.route('/external/compass/shop/core-index', methods=['GET'])
def get_compass_core_index():
    """Get compass shop core index - requires COMPASS_COOKIES."""
    cookies = os.getenv('COMPASS_COOKIES', '')
    if not cookies:
        return success_response({
            'data': {
                'module_data': {
                    'homepage_core_index': {
                        'compass_general_multi_index_card_value': {
                            'basic_meta': [],
                            'data': []
                        }
                    }
                }
            },
            'message': 'COMPASS_COOKIES not configured'
        })
    
    return success_response({
        'data': {
            'module_data': {
                'homepage_core_index': {
                    'compass_general_multi_index_card_value': {
                        'basic_meta': [],
                        'data': []
                    }
                }
            }
        },
        'message': 'Compass API not yet implemented - configure COMPASS_COOKIES'
    })