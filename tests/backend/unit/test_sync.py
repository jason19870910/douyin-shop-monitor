"""Tests for sync API endpoints and auth public endpoint policy."""
import os

os.environ.setdefault('SKIP_AUTH', 'true')
os.environ.setdefault('DATA_DIR', './data_test_sync')


def test_sync_not_in_public_endpoints():
    from app import PUBLIC_ENDPOINTS

    assert '/api/v1/sync' not in PUBLIC_ENDPOINTS
    assert '/api/v1/dashboard/stats' not in PUBLIC_ENDPOINTS
    assert '/api/v1/mock/status' not in PUBLIC_ENDPOINTS
    assert '/api/v1/health' in PUBLIC_ENDPOINTS


def test_sync_history_empty(tmp_path, monkeypatch):
    monkeypatch.setenv('SKIP_AUTH', 'true')
    monkeypatch.setenv('DATA_DIR', str(tmp_path))

    from app import app

    app.config['TESTING'] = True
    with app.test_client() as client:
        resp = client.get('/api/v1/sync/history')
        assert resp.status_code == 200
        body = resp.get_json()
        assert body['success'] is True
        assert 'list' in body['data']
        assert body['data']['total'] >= 0
