"""Accounts blueprint."""
from flask import Blueprint, request
from services.fetcher import cache, CACHE_KEYS, DEFAULT_ACCOUNTS
from datetime import datetime
from utils.responses import success_response, not_found_response, bad_request_response

accounts_bp = Blueprint('accounts', __name__, url_prefix='/api/v1')


@accounts_bp.route('/accounts', methods=['GET'])
def get_accounts():
    """Get account list with filtering."""
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 20))
    keyword = request.args.get('keyword', '').lower()
    status_filter = request.args.get('status')
    
    accounts = cache.get(CACHE_KEYS['accounts'], DEFAULT_ACCOUNTS)
    
    if keyword:
        accounts = [a for a in accounts if keyword in a.get('account_name', '').lower() or keyword in a.get('account_id', '').lower()]
    if status_filter:
        accounts = [a for a in accounts if a.get('status') == status_filter]
    
    total = len(accounts)
    start = (page - 1) * size
    end = start + size
    
    return success_response({
        'items': accounts[start:end],
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
    return success_response(account)


@accounts_bp.route('/accounts', methods=['POST'])
def create_account():
    """Create new account entry."""
    data = request.get_json()
    if not data:
        return bad_request_response('Invalid data')
    
    account = {
        'account_id': f"acc_{int(datetime.now().timestamp())}",
        'account_name': data.get('account_name', ''),
        'platform': data.get('platform', 'douyin'),
        'status': data.get('status', 'active'),
        'follower_count': data.get('follower_count', 0),
        'created_at': datetime.now().isoformat(),
    }
    
    accounts = cache.get(CACHE_KEYS['accounts'], DEFAULT_ACCOUNTS)
    accounts.insert(0, account)
    cache.set(CACHE_KEYS['accounts'], accounts)
    
    return success_response(account, 'Account created', 201)


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
    
    account.update({
        'account_name': data.get('account_name', account['account_name']),
        'status': data.get('status', account['status']),
        'follower_count': data.get('follower_count', account['follower_count']),
        'updated_at': datetime.now().isoformat()
    })
    
    cache.set(CACHE_KEYS['accounts'], accounts)
    return success_response(account, 'Account updated')


@accounts_bp.route('/accounts/<account_id>', methods=['DELETE'])
def delete_account(account_id: str):
    """Delete account entry."""
    accounts = cache.get(CACHE_KEYS['accounts'], DEFAULT_ACCOUNTS)
    account = next((a for a in accounts if a.get('account_id') == account_id), None)
    if not account:
        return not_found_response('Account')
    
    accounts = [a for a in accounts if a.get('account_id') != account_id]
    cache.set(CACHE_KEYS['accounts'], accounts)
    return success_response(None, 'Account deleted')