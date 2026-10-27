"""Accounts blueprint."""
from flask import Blueprint, request
from services.fetcher import cache, CACHE_KEYS, DEFAULT_ACCOUNTS, ACCOUNTS_FILE, save_json_file
from datetime import datetime
from utils.responses import success_response, not_found_response, bad_request_response

accounts_bp = Blueprint('accounts', __name__, url_prefix='/api/v1')


def _persist_accounts(accounts: list) -> None:
    """双写账号数据：Redis 持久化（无 TTL）+ JSON 文件，避免缓存过期后丢失。"""
    cache.set(CACHE_KEYS['accounts'], accounts, ttl=None)
    save_json_file(ACCOUNTS_FILE, accounts)


@accounts_bp.route('/accounts', methods=['GET'])
def get_accounts():
    """Get account list with filtering."""
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 20))
    keyword = request.args.get('keyword', '').lower()
    status_filter = request.args.get('status')
    
    accounts = cache.get(CACHE_KEYS['accounts'], DEFAULT_ACCOUNTS)
    
    # Transform to match frontend Account interface
    transformed_accounts = []
    for a in accounts:
        transformed_accounts.append({
            'account_id': a.get('account_id', ''),
            'account_name': a.get('account_name', ''),
            'account_type': a.get('account_type', a.get('platform', 'douyin')),
            'phone': a.get('phone', ''),
            'email': a.get('email', ''),
            'status': a.get('status', 'active'),
            'last_login': a.get('last_login'),
            'create_time': a.get('create_time', a.get('created_at', '')),
        })
    
    if keyword:
        transformed_accounts = [a for a in transformed_accounts if keyword in a.get('account_name', '').lower() or keyword in a.get('account_id', '').lower()]
    if status_filter:
        transformed_accounts = [a for a in transformed_accounts if a.get('status') == status_filter]
    
    total = len(transformed_accounts)
    start = (page - 1) * size
    end = start + size
    
    return success_response({
        'items': transformed_accounts[start:end],
        'total': total,
        'page': page,
        'size': size
    })


@accounts_bp.route('/accounts/<account_id>', methods=['GET'])
def get_account(account_id: str):
    """Get single account details."""
    accounts = cache.get(CACHE_KEYS['accounts'], DEFAULT_ACCOUNTS)
    account = next((a for a in accounts if a.get('account_id') == account_id), None)
    if not account:
        return not_found_response('Account')
    
    # Transform to match frontend Account interface
    transformed_account = {
        'account_id': account.get('account_id', ''),
        'account_name': account.get('account_name', ''),
        'account_type': account.get('account_type', account.get('platform', 'douyin')),
        'phone': account.get('phone', ''),
        'email': account.get('email', ''),
        'status': account.get('status', 'active'),
        'last_login': account.get('last_login'),
        'create_time': account.get('create_time', account.get('created_at', '')),
    }
    return success_response(transformed_account)


@accounts_bp.route('/accounts', methods=['POST'])
def create_account():
    """Create new account entry."""
    data = request.get_json()
    if not data:
        return bad_request_response('Invalid data')
    
    account = {
        'account_id': f"acc_{int(datetime.now().timestamp())}",
        'account_name': data.get('account_name', ''),
        'account_type': data.get('account_type', data.get('platform', 'douyin')),
        'platform': data.get('platform', 'douyin'),  # 兼容旧字段
        'phone': data.get('phone', ''),
        'email': data.get('email', ''),
        'status': data.get('status', 'active'),
        'follower_count': data.get('follower_count', 0),
        'last_login': data.get('last_login'),
        'create_time': datetime.now().isoformat(),
        'created_at': datetime.now().isoformat(),  # 兼容旧字段
    }
    
    accounts = cache.get(CACHE_KEYS['accounts'], DEFAULT_ACCOUNTS)
    accounts.insert(0, account)
    _persist_accounts(accounts)
    
    # Transform for response
    transformed_account = {
        'account_id': account['account_id'],
        'account_name': account['account_name'],
        'account_type': account['account_type'],
        'phone': account['phone'],
        'email': account['email'],
        'status': account['status'],
        'last_login': account['last_login'],
        'create_time': account['create_time'],
    }
    return success_response(transformed_account, 'Account created', 201)


@accounts_bp.route('/accounts/<account_id>', methods=['PUT'])
def update_account(account_id: str):
    """Update account entry."""
    accounts = cache.get(CACHE_KEYS['accounts'], DEFAULT_ACCOUNTS)
    account = next((a for a in accounts if a.get('account_id') == account_id), None)
    if not account:
        return not_found_response('Account')
    
    data = request.get_json()
    if not data:
        return bad_request_response('Invalid data')
    
    # Update with new fields
    if 'account_name' in data:
        account['account_name'] = data['account_name']
    if 'account_type' in data:
        account['account_type'] = data['account_type']
    if 'platform' in data:
        account['platform'] = data['platform']
    if 'phone' in data:
        account['phone'] = data['phone']
    if 'email' in data:
        account['email'] = data['email']
    if 'status' in data:
        account['status'] = data['status']
    if 'follower_count' in data:
        account['follower_count'] = data['follower_count']
    if 'last_login' in data:
        account['last_login'] = data['last_login']
    if 'create_time' in data:
        account['create_time'] = data['create_time']
    account['updated_at'] = datetime.now().isoformat()
    
    _persist_accounts(accounts)
    
    # Transform for response
    transformed_account = {
        'account_id': account['account_id'],
        'account_name': account.get('account_name', ''),
        'account_type': account.get('account_type', account.get('platform', 'douyin')),
        'phone': account.get('phone', ''),
        'email': account.get('email', ''),
        'status': account.get('status', 'active'),
        'last_login': account.get('last_login'),
        'create_time': account.get('create_time', account.get('created_at', '')),
    }
    return success_response(transformed_account, 'Account updated')


@accounts_bp.route('/accounts/<account_id>', methods=['DELETE'])
def delete_account(account_id: str):
    """Delete account entry."""
    accounts = cache.get(CACHE_KEYS['accounts'], DEFAULT_ACCOUNTS)
    account = next((a for a in accounts if a.get('account_id') == account_id), None)
    if not account:
        return not_found_response('Account')
    
    accounts = [a for a in accounts if a.get('account_id') != account_id]
    _persist_accounts(accounts)
    return success_response(None, 'Account deleted')